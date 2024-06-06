""" Initialize and return the distance matrix for the MOA problem."""
function init_mats(model)
    n_ids = length(keys(model.config.ids))
    distance_matrix = ones(n_ids, n_ids)

    for (country, neighbors) in model.config.pipes
        x = model.config.ids[country]
        for neighbor in neighbors
            y = model.config.ids[neighbor]
            factor = 1 / ((1 - model.config.transport_loss)^model.config.distances[country, neighbor])
            distance_matrix[x, y] = factor
            distance_matrix[y, x] = factor
        end
    end

    return distance_matrix
end

"""
Create solver for the MOA problem.

In the current implementation we have a tuple (two solvers) for each snapshot.
"""
function create_solver(model, distance_matrix, source, target)
    solver1 = Model(() -> DiffOpt.diff_optimizer(HiGHS.Optimizer))
    solver2 = Model(() -> DiffOpt.diff_optimizer(HiGHS.Optimizer))
    set_silent.([solver1, solver2])
    n = size(distance_matrix, 1)
    magic_number = 1000000

    function set_common_constraints!(solver)
        # Variable definition
        @variable(solver, f[i = 1:n, j = 1:n; near(model, i, j)] ≥ 0)
        # Capacity constraints are modified in the max_flow_lp function; right now we set all to magic_number
        @constraint(solver, upper[i = 1:n, j = 1:n; near(model, i, j)], f[i, j] ≤ magic_number)
        # Flow conservation constraints with losses
        @constraint(solver, [i = 1:n; i ≠ source && i ≠ target], sum(f[:, i]) == sum(distance_matrix[j, i] * f[i, j] for j in 1:n if near(model, i, j)))
    end

    set_common_constraints!.([solver1, solver2])

    # Maximize used energy
    @objective(solver1, Max, sum(solver1[:f][:, 2]))
    
    # Minimize wasted energy
    @constraint(solver2, result, sum(solver2[:f][:, 2]) ≥ magic_number)
    @objective(solver2, Min, sum(solver2[:f][1, :]))

    return (solver1, solver2)
end

""" Initialize MOA solver for each snapshot. """
function init_all_solvers!(model)
    dist_mat = init_mats(model)
    solvers = [create_solver(model, dist_mat, 1, 2) for _ in axes(model.loads, 1)]
    n = size(dist_mat, 1)
    Containers.@container(flow[i = 1:n, j = 1:n; near(model, i, j)], 1.0) # for backpropagation
    flows = fill(flow, length(solvers))
    append!(model.solvers, solvers)
    append!(model.flows, flows)
end

"""
Check whether two nodes are connected by a pipe.

This includes the start and end nodes connected via generation/load.
"""
function near(model, x, y)
    name_x = findfirst(isequal(x), model.config.ids)
    name_y = findfirst(isequal(y), model.config.ids)
    if name_x in keys(model.config.pipes)
        if name_y in model.config.pipes[name_x]
            return true
        end
    end
    if name_y in keys(model.config.pipes)
        if name_x in model.config.pipes[name_y]
            return true
        end
    end

    return (name_x == "start" ≠ name_y) ⊻ (name_y == "end" ≠ name_x)
end

function set_bounds!(con1, con2, capacities, hypo, loads, pipes, ids, snapshot)

    function set!(i, j, c)
        if eltype(con1) <: ConstraintRef # for backpropagation
            set_normalized_rhs(con1[i, j], c)
            set_normalized_rhs(con2[i, j], c)
        else
            con1[i, j] = c
            con2[i, j] = c
        end
    end

    for key in axes(hypo, 2)
        if key in [ids["start"], ids["end"]]
            continue
        end
        generation = hypo[snapshot, key]
        loading = loads[snapshot, key]
        set!(ids["start"], key, generation)
        set!(key, ids["end"], loading)
    end

    for (country, vals) in pipes
        x = ids[country]
        for neighbor in vals
            y = ids[neighbor]
            set!(x, y, capacities[x, y])
            set!(y, x, capacities[x, y])
        end
    end
    return nothing
end

""" Return the flow matrix for our MOA-LP-model. """
function max_flow_lp(capacities, model, hypo, snapshot)
    solver = model.solvers[snapshot]

    set_bounds!(
        solver[1][:upper], solver[2][:upper],
        capacities, hypo, model.loads, model.config.pipes, model.config.ids, snapshot
    )

    check(solver) = @assert is_solved_and_feasible(solver) (
        println(solver); println(termination_status(solver)); snapshot
    )

    JuMP.optimize!(solver[1])
    check(solver[1])
    set_normalized_rhs(solver[2][:result], JuMP.objective_value(solver[1]))
    JuMP.optimize!(solver[2])
    check(solver[2])
    val = value.(solver[2][:f])

    return val
end
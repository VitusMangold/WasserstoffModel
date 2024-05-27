function init_mats(model)
    n_ids = length(keys(model.config.ids))
    distance_matrix = zeros(n_ids, n_ids)

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

function init_all_solvers!(model)
    dist_mat = init_mats(model)
    solvers = [create_solver(model, dist_mat, 1, 2) for _ in axes(model.loads, 1)]
    append!(model.solvers, solvers)
end

function create_solver(model, distance_matrix, source, target)
    solver = Model(() -> MOA.Optimizer(HiGHS.Optimizer))
    # solver = Model(() -> DiffOpt.diff_optimizer(optimizer_with_attributes(HiGHS.Optimizer, "log_to_console" => false)))
    # solver = Model(() -> DiffOpt.diff_optimizer(HiGHS.Optimizer))
    # solver = Model(HiGHS.Optimizer)
    set_silent(solver)
    n = size(distance_matrix, 1)
    @variable(solver, f[i = 1:n, j = 1:n; near(model, i, j)] >= 0)
    @constraint(solver, upper[i = 1:n, j = 1:n; near(model, i, j)], f[i, j] <= 1000000)
    # Capacity constraints are modified in the max_flow_lp function; right now we set all to 0.0
    # Flow conservation constraints
    @constraint(solver, [i = 1:n; i != source && i != target], sum(f[:, i]) == sum(distance_matrix[j, i] * f[i, j] for j in 1:n if near(model, i, j)))
    # @objective(solver, Max, sum(f[:, 2]))
    @objective(solver, Max, [sum(f[:, 2]), -sum(f[1, :])])
    set_attribute(solver, MOA.Algorithm(), MOA.Hierarchical())
    set_attribute.(solver, MOA.ObjectivePriority.(1:2), [2, 1])
    return solver
end

function max_flow_lp(capacities, model, hypo, snapshot)
    solver = model.solvers[snapshot]

    function set!(i, j, c)
        set_normalized_rhs(solver[:upper][i, j], c)
    end

    for key in names(hypo, 2)
        if key in ["start", "end"]
            continue
        end
        generation = hypo[snapshot, key]
        loading = model.loads[snapshot, key]
        set!(model.config.ids["start"], model.config.ids[key], generation)
        set!(model.config.ids[key], model.config.ids["end"], loading)
    end

    for (country, vals) in model.config.pipes
        x = model.config.ids[country]
        for neighbor in vals
            y = model.config.ids[neighbor]
            set!(x, y, capacities[x, y])
            set!(y, x, capacities[x, y])
        end
    end
    JuMP.optimize!(solver)
    @assert is_solved_and_feasible(solver)
    val = value.(solver[:f])

    return val
end
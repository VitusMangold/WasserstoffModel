function init_mats(model)
    n_nodes = length(model.ids)
    distance_matrix = zeros(n_nodes, n_nodes)

    for (country, neighbors) in model.distances
        x = model.ids[country]
        for neighbor in keys(neighbors)
            y = model.ids[neighbor]
            factor = 1 / ((1 - model.transport_loss)^model.distances[country][neighbor])
            distance_matrix[x, y] = factor
            distance_matrix[y, x] = factor
        end
    end

    return distance_matrix
end

function init_all_solvers!(model)
    dist_mat = init_mats(model)
    solvers = [create_solver(dist_mat, 1, 2) for _ in eachindex(model.loads["DE"])]
    append!(model.solvers, solvers)
end

function create_solver(distance_matrix, source, target)
    solver = Model(() -> DiffOpt.diff_optimizer(optimizer_with_attributes(HiGHS.Optimizer, "log_to_console" => false)))
    set_silent(solver)
    n = size(distance_matrix, 1)
    @variable(solver, f[1:n, 1:n] >= 0)
    # Capacity constraints are modified in the max_flow_lp function; right now we set all to 0.0
    @constraint(solver, f[1:n, 1:n] .<= 0)
    # Flow conservation constraints
    @constraint(solver, [i = 1:n; i != source && i != target], sum(f[i, :]) == sum(distance_matrix[:, i] .* f[:, i]))
    @objective(solver, Max, sum(f[:, 2]))
    return solver
end

function max_flow_lp(capacities, model, hypo, snapshot)
    solver = model.solvers[snapshot]

    set!(i, j, c) = set_upper_bound(solver[:f][i, j], c)

    for key in keys(model.net_dict)
        generation = hypo[key][snapshot]
        loading = model.loads[key][snapshot]
        set!(model.ids["start"], model.ids[key], generation)
        set!(model.ids[key], model.ids["end"], loading)
    end

    for (country, neighbors) in capacities
        x = model.ids[country]
        for (neighbor, capacity) in neighbors
            y = model.ids[neighbor]
            set!(x, y, capacity)
            set!(y, x, capacity)
        end
    end
    # println(solver)
    JuMP.optimize!(solver)
    @assert is_solved_and_feasible(solver)
    objective_value(solver)
    return nothing, value.(solver[:f])
end

function ChainRulesCore.rrule(::typeof(matrix_relu), y::Matrix{T}) where {T}
    model = Model(() -> DiffOpt.diff_optimizer(Ipopt.Optimizer))
    pv = matrix_relu(y; model = model)
    function pullback_matrix_relu(dl_dx)
        # some value from the backpropagation (e.g., loss) is denoted by `l`
        # so `dl_dy` is the derivative of `l` wrt `y`
        x = model[:x] # load decision variable `x` into scope
        dl_dy = zeros(T, size(dl_dx))
        dl_dq = zeros(T, size(dl_dx))
        # set sensitivities
        MOI.set.(model, DiffOpt.ReverseVariablePrimal(), x[:], dl_dx[:])
        # compute grad
        DiffOpt.reverse_differentiate!(model)
        # return gradient wrt objective function parameters
        obj_exp = MOI.get(model, DiffOpt.ReverseObjectiveFunction())
        # coeff of `x` in q'x = -2y'x
        dl_dq[:] .= JuMP.coefficient.(obj_exp, x[:])
        dq_dy = -2 # dq/dy = -2
        dl_dy[:] .= dl_dq[:] * dq_dy
        return (ChainRulesCore.NoTangent(), dl_dy)
    end
    return pv, pullback_matrix_relu
end
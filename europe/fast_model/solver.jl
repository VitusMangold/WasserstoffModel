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
    # solver = Model(() -> DiffOpt.diff_optimizer(optimizer_with_attributes(HiGHS.Optimizer, "log_to_console" => false)))
    solver = Model(() -> DiffOpt.diff_optimizer(HiGHS.Optimizer))
    # solver = Model(HiGHS.Optimizer)
    set_silent(solver)
    n = size(distance_matrix, 1)
    @variable(solver, f[i = 1:n, j = 1:n; near(model, i, j)] >= 0)
    @constraint(solver, upper[i = 1:n, j = 1:n; near(model, i, j)], f[i, j] <= 1000000)
    # Capacity constraints are modified in the max_flow_lp function; right now we set all to 0.0
    # Flow conservation constraints
    @constraint(solver, [i = 1:n; i != source && i != target], sum(f[:, i]) == sum(distance_matrix[j, i] * f[i, j] for j in 1:n if near(model, i, j)))
    @objective(solver, Max, sum(f[:, 2]))
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

function ChainRulesCore.rrule(::typeof(max_flow_lp), model, snapshot)
    solver = model.solvers[snapshot]
    for (country, neighbors) in model.dnet_dict
        x = model.config.ids[country]
        for (neighbor, capacity) in neighbors
            y = model.config.ids[neighbor]
            # MOI.set.(solver, DiffOpt.ReverseVariablePrimal(), solver[:f], 1.0)
        end
    end
    DiffOpt.reverse_differentiate!(solver)
    obj_exp = MOI.get.(solver, DiffOpt.ReverseConstraintFunction(), solver[:upper])
    grad = JuMP.constant.(obj_exp)
    return grad
end

function near(model, x, y)
    name_x = findfirst(isequal(x), model.config.ids)
    name_y = findfirst(isequal(y), model.config.ids)
    dist = model.config.distances
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

    return (name_x == "start" != name_y) ⊻ (name_y == "end" != name_x)
end

function ChainRulesCore.rrule(::typeof(costs), cap::OrderedDict, shares::OrderedDict)
    function pullback_flow(dcosts_dnet)

    end
    Threads.@threads for snapshot in snapshots
        F, grad = max_flow_lp(capacities, model, hypo, snapshot)
        calc_net_flow!(model=model, flow_matrix=F, hypo=hypo, snapshot=snapshot)
        if snapshot == 1
            # println(F)
            # println(grad)
            println("Hier")
        end
    end
end

function ChainRulesCore.rrule(::typeof(costs), cap::OrderedDict, shares::OrderedDict)
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
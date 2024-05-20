function find_optimum(model; scenario, n_chunks=60)

    n_leaves = count_leaves(model.distances)

    initial_cap = Dict(
        key => Dict(neighbor => 100.0 for neighbor in keys(value))
        for (key, value) in model.distances
    )
    initial_share = Dict(key => 1.0 for key in keys(model.hypothetical))

    trunc = x -> x
    expand = x -> x

    function transform(input)
        x = expand(input)
        next = iterate(x)
        for (key, value) in model.distances
            for neighbor in keys(value)
                (val, state) = next
                initial_cap[key][neighbor] = val
                next = iterate(x, state)
            end
        end
        for key in keys(model.hypothetical)
            (val, state) = next
            initial_share[key] = val
            next = iterate(x, state)
        end

        return initial_cap, initial_share
    end

    if scenario == :all # optimize everything
    elseif scenario == :same # the same share for every country
        trunc = input -> vcat(input[1:n_leaves], input[n_leaves + 1])
        expand = input -> vcat(input[1:n_leaves], [input[end] for _ in initial_share])
    elseif scenario == :fixed # 100% shares and optimize capacities
        trunc = input -> input[1:n_leaves]
        expand = input -> vcat(input, [1.0 for _ in initial_share])
    elseif scenario == :no_cap_fixed # the same share for every country and don't use capacities
        trunc = input -> input[n_leaves + 1:end]
        expand = input -> vcat(fill(0.0, n_leaves), input)
    elseif scenario == :no_cap # the same share for every country and don't use capacities
        trunc = input -> [input[end]]
        expand = input -> vcat(fill(0.0, n_leaves), [input[1] for _ in initial_share])
    elseif scenario == :nothing # 100% shares and don't use capacities
        return transform([fill(0.0, n_leaves); [1.0 for _ in initial_share]])
    else
        AssertionError("Scenario not implemented")
    end

    # Define the cost function to be minimized; parameters are redundant for now
    cost_function = (x, p) -> costs(model, transform(x)...)

    lower = [[0.0 for _ in 1:n_leaves]; [0.0 for _ in initial_share]]
    upper = [[100000. for _ in 1:n_leaves]; [3.0 for _ in initial_share]]
    initial = [[1000.0 for _ in 1:n_leaves]; [1.0 for _ in initial_share]]

    println(trunc(initial))

    # Optimization problem
    prob = OptimizationProblem(
        cost_function,
        trunc(initial),
        lb = trunc(lower),
        ub = trunc(upper),
        sense = MinSense
    )

    # Solution
    # results = solve(prob, OptimizationOptimJL.BFGS(), maxtime=600) # 150s
    results = solve(prob, NLopt.LN_NELDERMEAD(), maxtime=3600 * 8) # 9h
    # results = solve(prob, NLopt.LN_COBYLA, maxtime=1200) # ~ 600s stuck in local minimum
    # results = solve(prob, NLopt.LN_BOBYQA, maxtime=1200) # ~ stuck 65s in local minimum

    # Print whether the optimization was successful
    println("Optimization status: ", results.retcode)
    println("Min value: ", results.objective)

    # Extract the minimizer and transform it back if necessary
    return transform(results.u)
end
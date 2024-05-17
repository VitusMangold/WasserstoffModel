using JuMP
using HiGHS

function create_solver(cap, source, target)
    solver = direct_model(optimizer_with_attributes(HiGHS.Optimizer, "log_to_console" => false))
    n = size(cap, 1)
    @variable(solver, f[1:n, 1:n] >= 0)
    # Capacity constraints
    @constraint(solver, con[i = 1:n, j = 1:n], f[i, j] <= cap[i, j])
    # Flow conservation constraints
    @constraint(solver, [i = 1:n; i != source && i != target], sum(f[i, :]) == sum(f[:, i]))
    @objective(solver, Max, sum(f[1, :]))
    return solver
end

function max_flow_lp(solver, cap)
    n = size(cap, 1)
    # modify_coefficients!(solver, solver[:con], cap)
    for i in 1:n
        for j in 1:n
            set_upper_bound(solver[:con][i, j], cap[i, j])
        end
    end
    optimize!(solver)
    @assert is_solved_and_feasible(solver)
    objective_value(solver)
    return nothing, value.(f)
end

function modify_coefficients!(model, variable, C)
    for j in axes(C, 2)  # Loop over the columns of C (each variable)
        set_normalized_coefficient.(model[:con], variable[j], vec(C[:, j]))
    end
end
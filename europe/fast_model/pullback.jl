function ChainRulesCore.rrule(::typeof(sum_costs), )
    function pullback(dcosts)
        return nothing
    end
    return pullback
end

function ChainRulesCore.rrule(::typeof(max_flow_lp), model, dcapacities, dhypo, snapshot)
    function pullback(dcapacities)
        return nothing, nothing, nothing
    end
    return pullback
end

Enzyme.autodiff(costs, Const(model), Duplicated(capacities, dcapacities), Duplicated(share_ren, dshare_ren))
function test(x, n_chunks=48)

    initial_cap = Dict(
        key => Dict(neighbor => 1000.0 for neighbor in keys(value))
        for (key, value) in model.distances
    )
    initial_share = Dict(key => 1.0 for key in keys(model.hypothetical))

    function transform(x)
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

    # Define the cost function to be minimized
    return costs(model, transform(x)..., n_chunks)
end

x = [[100.0 for _ in 1:22]; [1.1 for _ in 1:12]]
test(x)
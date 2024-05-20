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

    res = (Dict("IT" => Dict("AT" => 1579.28019895756, "CH" => 1320.6590150632737), "AT" => Dict("CZ" => 2522.824733822867), "ES" => Dict(), "LU" => Dict("FR" => 1931.7140020765755), "CH" => Dict("AT" => 986.4185414069334), "DE" => Dict("BE" => 720.708798034766, "AT" => 2254.0443848326613, "LU" => 488.8497952582636, "CZ" => 2135.9082698401894, "CH" => 2360.721747725866, "FR" => 2409.1176180013545, "PL" => 1184.6305016952622, "DK" => 826.4956941272881, "NL" => 1678.722219996272), "NL" => Dict("BE" => 2133.0267156806817, "DK" => 327.00955161969483), "BE" => Dict("LU" => 1087.4975541970662, "FR" => 3065.6043039894557), "CZ" => Dict("PL" => 2266.989068338143), "FR" => Dict("IT" => 2217.1634675545697, "ES" => 683.0002435188679, "CH" => 1884.02081786355), "PL" => Dict(), "DK" => Dict()), Dict("AT" => 0.9960124007100002, "ES" => 0.9965090773994545, "IT" => 1.2962778285432206, "LU" => 1.7602445807884104, "CH" => 1.332197046095905, "DE" => 1.14042871936651, "NL" => 1.1911928086837662, "BE" => 1.165400276581185, "CZ" => 0.8710974547098495, "FR" => 0.9734761965348073, "PL" => 1.2516563914665058, "DK" => 1.1872998156016767))

    # Define the cost function to be minimized
    # return costs(model, res...)
    return costs(model, transform(x)...)
end

x = [[100.0 for _ in 1:22]; [1.1 for _ in 1:12]]

# JuMP._CONSTRAINT_LIMIT_FOR_PRINTING[] = 1000
# # @time for i in 1:10
# #     test([[100.0 + 100*i for _ in 1:22]; [1.0 for _ in 1:12]])
# end
@time test(x)
layer = PerturbedMultiplicative(test; ε=0.1, nb_samples=5)
layer(x)
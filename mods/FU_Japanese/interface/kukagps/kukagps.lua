-- THIS IS THE FRACKIN RACES ONE
require "/scripts/util.lua"

MATERIALS = "materialList.materials"

function init()
        populateMaterialsList()
end

function addText(text)
	local path = string.format("%s.%s.text", MATERIALS, widget.addListItem(MATERIALS))
	widget.setText(path, text)
end

function addSeparator()
        addText("-------------------------------------------------------------------------------")
end

function populateMaterialsList()
        widget.clearListItems(MATERIALS)
        local worldId = string_split(player.worldId(),":")
        local planet = {location = {tonumber(worldId[2]),tonumber(worldId[3]),tonumber(worldId[4])}, planet = tonumber(worldId[5]), satellite = (tonumber(worldId[6]) or 0)}
        local system ={location = {tonumber(worldId[2]),tonumber(worldId[3]),tonumber(worldId[4])}}

        if worldId[1]=="InstanceWorld" then
            addText("ここはインスタンスワールドです")

            -- More info about the dungeon could be added here
        elseif worldId[1]=="ClientShipWorld" then
                addText("ここは船内ワールドです")

                local shipInfo = player.shipUpgrades()
                local isBYOS = world.getProperty("fu_byos")

                if isBYOS then
                    addText("^green;船の種類：^reset;自由建造船（BYOS）")
                    addText("船体の外壁を採掘すると拡張できます。アップグレード用クエストはありません。")

                    if (world.getProperty("fu_byos.systemTravel") or 0) > 0 then
                        addText("^green;エンジン状態^reset;：^yellow;超光速ドライブ^reset;が正常稼働中（どこへでも移動可能）。")
                    elseif (world.getProperty("fu_byos.planetTravel") or 0) > 0 then
                        addText("^green;エンジン状態^reset;：^yellow;亜光速ドライブ^reset;（星系内を移動可能）。")
                        addText("ほかの星系へ行くには^yellow;小型超光速ドライブ^reset;に交換してください。")
                        addText("補足：エンジンの種類にかかわらず、星系内の移動では燃料を消費しません。")
                    else
                        addText("^green;エンジン状態^reset;：^red;停止中^reset;（稼働するエンジンが見つかりません）。")
                        addText("^yellow;亜光速ドライブ^reset;か^yellow;小型超光速ドライブ^reset;を船内のどこかに設置すると修復できます。")
                    end
                else
                    addText("^green;船の種類：^reset;標準の船（自由建造船ではありません）")

                    local shipLevel = shipInfo.shipLevel or 0
                    addText("^green;船の段階：^reset; " .. shipLevel)

                    if not contains(player.shipUpgrades().capabilities, "systemTravel") then
                        addText("^green;エンジン状態^reset;：^red;停止中^reset;（未修理）。")
                        addText("標準の前哨基地でエスター・ブライトに会うと、その場で船が修理されます。")
                    else
                        addText("^green;エンジン状態^reset;：^yellow;正常稼働中^reset;。")
                        if shipLevel < 8 then
                            addText("標準のゲームと同じく、^yellow;乗組員^reset;か^yellow;ライセンス^reset;で拡張できます。")
                        else
                            addText("最大サイズです（これ以上は拡張できません）。")
                        end
                    end
                end

                addSeparator()

                addText(string.format(
                    "^green;燃料消費の軽減率：^reset; %.f%%",
                    100 * (shipInfo.fuelEfficiency or 0)
                ))
                addText("^green;最大燃料：^reset; " .. (shipInfo.maxFuel or '?'))
                addText("^green;船速（星系内）：^reset; " .. (shipInfo.shipSpeed or '?'))

                -- TODO: add information about the crew limits, etc.
        elseif worldId[1]=="CelestialWorld" then
            dungeons =root.assetJson("/interface/kukagps/dungeons.config")
            weather =root.assetJson("/interface/kukagps/weather.config")
            enviroment =root.assetJson("/interface/kukagps/enviroment.config")
            ores =root.assetJson("/interface/kukagps/ores.config")
            biomes =root.assetJson("/interface/kukagps/biomes.config")
            stars =root.assetJson("/interface/kukagps/stars.config")

            -- print system
            addText("^green;星系：^reset; "..celestial.planetName(system))

            local starType = celestial.planetParameters(system).typeName or "default"
            -- print star
            addText("^green;恒星：^reset; " .. (stars[starType] or '?'))

            -- print coord
            addText("^green;X座標：^reset; "..system.location[1].."                        ^green;Y座標：^reset; "..system.location[2])

            -- print planet
            addText("^green;惑星：^reset; "..celestial.planetName(planet))

            -- print planet primary biome
            local parameters = celestial.visitableParameters(planet)
            addText("                                                ^green;バイオーム：^reset; ")

            local anomaliesFound=false
            local worldSize = world.size() or {0,0}

            -- Search for biomes.
            local function showLayer(layer, layerName, layerAbove, biomeColors)
                if not layer then return end

                local biomeCodes = {
                    layer.primaryRegion.biome,
                    layer.primarySubRegion.biome
                }
                for _, region in pairs(layer.secondaryRegions) do
                    table.insert(biomeCodes, region.biome)
                end
                for _, region in pairs(layer.secondarySubRegions) do
                    table.insert(biomeCodes, region.biome)
                end

                -- Remove duplicates, but preserve the order.
                local uniqueBiomeCodes = {}
                local alreadyListed = {}
                for _, biomeCode in ipairs(biomeCodes) do
                    if not alreadyListed[biomeCode] then
                        table.insert(uniqueBiomeCodes, biomeCode)
                        alreadyListed[biomeCode] = true
                    end
                end

                local listedBiomeNames = {}
                for _, biomeCode in ipairs(uniqueBiomeCodes) do
                    if isHiddenBiome(biomeCode) then
                        -- Semi-secret biomes like Precursor Underground are not listed.
                        anomaliesFound = true
                    else
                        local biomeName = biomes[biomeCode] or biomeCode
                        local biomeColor = biomeColors and biomeColors[biomeCode]
                        if biomeColor then
                            biomeName = string.format("^%s;%s^reset;", biomeColor, biomeName)
                        end

                        table.insert(listedBiomeNames, biomeName)
                    end
                end

                local biomesDescription
                if #listedBiomeNames == 0 then
                    -- The only biome is secret. Not really secret in this situation...
                    biomesDescription = "（スキャンで特定できません）"
                else
                    biomesDescription = table.concat(listedBiomeNames, ', ') .. '.'
                end

                local value = string.format("^green;%s^reset; [%s-%s]: %s",
                    layerName,
                    layer.layerMinHeight,
                    layerAbove and layerAbove.layerMinHeight or worldSize[2],
                    biomesDescription
                )
                addText(value)
            end

            showLayer(parameters.spaceLayer, "宇宙層")
            showLayer(parameters.atmosphereLayer, "大気層", parameters.spaceLayer)
            if parameters.surfaceLayer then
                showLayer(parameters.surfaceLayer, "地表層", parameters.atmosphereLayer,
                    { [parameters.surfaceLayer.primaryRegion.biome] = "yellow" }
                )
            end
            showLayer(parameters.subsurfaceLayer, "地表直下層", parameters.surfaceLayer)

            local layerAboveCore
            if parameters.undergroundLayers then
                showLayer(parameters.undergroundLayers[1], "地下第1層", parameters.subsurfaceLayer)
                showLayer(parameters.undergroundLayers[2], "地下第2層", parameters.undergroundLayers[1])
                showLayer(parameters.undergroundLayers[3], "地下第3層", parameters.undergroundLayers[2])
                layerAboveCore = parameters.undergroundLayers[#parameters.undergroundLayers]
            end
            showLayer(parameters.coreLayer, "核の層", layerAboveCore or parameters.subsurfaceLayer)

            -- anomalies found?
            if anomaliesFound then
                addText("^red;これらの層で異常を検出しました…^reset; ")
            end

            local pos = world.entityPosition(player.id())
            -- print pos
            addText("^green;現在のX座標：^reset; "..math.floor(pos[1]).."                                       ^green;現在のY座標：^reset; "..math.floor(pos[2]))

            -- print world size
            addText("^green;幅：^reset; "..worldSize[1].."                                            ^green;高さ：^reset; "..worldSize[2])

            -- print planet threat and gravity
            addText(string.format("^green;惑星の段階／脅威度：^reset; %.2f", parameters.threatLevel))
            addText("^green;重力：^reset; "..(parameters.gravity or 0))

            -- print planet ores names
            addText("^green;鉱石：^reset; ")
            local localOres="なし"
            local linecount=0
            for _,ore in pairs(celestial.planetOres(planet, (parameters.threatLevel or 0))) do
                if localOres=="なし" then
                    localOres = (ores[ore] or ore)
                else
                    localOres = localOres..", "..(ores[ore] or ore)
                end
                linecount = linecount+1
                if linecount==7 then
                    -- print line and reset counter
                    localOres = localOres.."."
                    addText("       "..localOres)
                    localOres = "なし"
                    linecount = 0
                end
            end
            if linecount ~= 0 then
                localOres = localOres.."."
                addText("       "..localOres)
            end

            addSeparator()

            if parameters.primaryBiome then -- asteroid fields don't have time in the typical sense
                -- print date
                addText("^green;日付：^reset; "..getDate(world.day()))

                -- print time
                addText("^green;時刻：^reset; "..timeConversion())

                -- print day length
                addText("^green;1日の長さ：^reset; "..math.floor(world.dayLength()))
            end

            -- print light level
            local lightLevel = math.floor(world.lightLevel(world.entityPosition(player.id()))*100)/100
            addText("^green;明るさ：^reset; "..lightLevel)

            -- print windLevel
            local windLevel = math.floor(world.windLevel(world.entityPosition(player.id()))*100)/100
            addText("^green;風の強さ：^reset; "..windLevel)

            -- print enviroment status effects
            local enviro="なし"
            for _,env in pairs(parameters.environmentStatusEffects) do
                if enviro=="なし" then
                    -- its the first.
                    enviro = enviroment[env] or env
                else
                    -- its NOT the first. Add comma.
                    enviro = enviro..", "..(enviroment[env] or env)
                end
            end

            addSeparator()

            enviro = enviro.."."
            addText("^green;環境による状態効果：^reset; "..enviro)

            addSeparator()

            addText("^green;天候：^reset; ")

            local weatherItem="なし"
            linecount=0
            for _,w in pairs(parameters.weatherPool) do
                ww = (w.weight * 100)
                if weatherItem=="なし" then
                    -- its the first.
                    weatherItem = (weather[w.item] or w.item).."("..ww.."%)"
                else
                    -- its NOT the first. Add comma.
                    weatherItem = weatherItem..", "..(weather[w.item] or w.item).."("..ww.."%)"
                end
                linecount = linecount+1
                if linecount==4 then
                    -- after 4 elements, print line and reset counter

                    weatherItem = weatherItem.."."
                    addText("          "..weatherItem)  -- print a long tab space, and then a line of weather info
                    weatherItem = "なし"
                    linecount = 0
                end
            end
            if linecount ~= 0 then
                weatherItem = weatherItem.."."
                addText("          "..weatherItem)
            end

            addSeparator()

            -- print dungeons
            addText("^green;惑星内のダンジョン：^reset; ")

            -- Search for dungeons in spaceLayer. If exists in dungeon's list, look for name. Else, unknown dungeon.
            if (parameters.spaceLayer and parameters.spaceLayer.dungeons) then
                for _,dungeon in pairs(parameters.spaceLayer.dungeons) do
                    addText(dungeons[dungeon] or "不明［"..dungeon.."]")
                end
            end
            -- Search for dungeons in atmosphereLayer. If exists in dungeon's list, look for name. Else, unknown dungeon.
            if (parameters.atmosphereLayer and parameters.atmosphereLayer.dungeons) then
                for _,dungeon in pairs(parameters.atmosphereLayer.dungeons) do
                    addText(dungeons[dungeon] or "不明［"..dungeon.."]")
                end
            end
            -- Search for dungeons in surfaceLayer. If exists in dungeon's list, look for name. Else, unknown dungeon.
            if (parameters.surfaceLayer and parameters.surfaceLayer.dungeons) then
                for _,dungeon in pairs(parameters.surfaceLayer.dungeons) do
                    addText(dungeons[dungeon] or "不明［"..dungeon.."]")
                end
            end
            -- Search for dungeons in subsurfaceLayer. If exists in dungeon's list, look for name. Else, unknown dungeon.
            if (parameters.subsurfaceLayer and parameters.subsurfaceLayer.dungeons) then
                for _,dungeon in pairs(parameters.subsurfaceLayer.dungeons) do
                    addText(dungeons[dungeon] or "不明［"..dungeon.."]")
                end
            end
            -- Search for dungeons in undergroundLayers. If exists in dungeon's list, look for name. Else, unknown dungeon.
            if (parameters.undergroundLayers) then
                for _,layer in pairs(parameters.undergroundLayers) do
                    -- you have to go in every layer inside undergroundLayers
                    for _,dungeon in pairs(layer.dungeons) do
                        addText(dungeons[dungeon] or "不明［"..dungeon.."]")
                    end
                end
            end
            -- Search for dungeons in corelayer. If exists in dungeon's list, look for name. Else, unknown dungeon.
            if (parameters.coreLayer and parameters.coreLayer.dungeons) then
                for _,dungeon in pairs(parameters.coreLayer.dungeons) do
                    addText(dungeons[dungeon] or "不明［"..dungeon.."]")
                end
            end
        else
            -- no ship, no dungeon/instance and no world.......Where the fuck are you?
            addText("エラーが発生しました")
        end
end

-- contribution of zimberzimber
function string_split(str, pat)
    local t = {}  -- NOTE: use {n = 0} in Lua-5.0
    local fpat = "(.-)" .. pat
    local last_end = 1
    local s, e, cap = str:find(fpat, 1)
    while s do
        if s ~= 1 or cap ~= "" then
            table.insert(t, cap)
        end
        last_end = e+1
        s, e, cap = str:find(fpat, last_end)
        end
        if last_end <= #str then
            cap = str:sub(last_end)
            table.insert(t, cap)
        end
        return t
end

function timeConversion()
        -- Hubnester time conversion function
        hubTime = (world.timeOfDay() + 0.25) * 24    -- the 0.25 is to make 0 am = 6 am (when the day starts)
        if hubTime > 12 then
            hubTime = hubTime - 12
            hubTimeModifier = " 午後"
            if hubTime > 12 then
                hubTime = hubTime - 12
                hubTimeModifier = " 午前"
                if hubTime < 1 then
                    hubTime = hubTime + 12
                end
            elseif hubTime < 1 then
                hubTime = hubTime + 12
            end
        else
            hubTimeModifier = " 午前"
        end
        hubHours = math.floor(hubTime, 0)
        hubMinutes = math.floor((hubTime - hubHours) * 60)
        if hubMinutes < 10 then
            hubMinutes = "0" .. tostring(hubMinutes)
        end
        return tostring(hubHours) .. ":" .. tostring(hubMinutes) .. tostring(hubTimeModifier)
end

function getDate(days)
    local month=1
    local daysperyear=365.242
	local year = math.floor(days / daysperyear)
	days = math.floor(days % daysperyear)
    local dayspermonth={31,28,31,30,31,30,31,31,30,31,30,31}
    if ((year%4)==0) or (((year%100)==0) and ((year%400)==0)) then
       dayspermonth={31,29,31,30,31,30,31,31,30,31,30,31}
    end
    while (days>=dayspermonth[month]) do
       days=days-dayspermonth[month]
       month=month+1
    end
    days=days+1
    return "年："..year.."、月："..month.."、日："..days
end

local precursorBiomes = {
    precursorsurface = true,
    precursorunderground = true
}
local elderBiomes = {
    atropuselder = true,
    atropuselderunderground = true,
    elder = true,
    elderunderground = true,
    shoggothbiome = true
}

function isHiddenBiome(biomeCode)
    if precursorBiomes[biomeCode] then
        return not player.hasCompletedQuest("precursor_unlock")
    elseif elderBiomes[biomeCode] then
        return not player.hasQuest('create_elder')
    end

    return false
end

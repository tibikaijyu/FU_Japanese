require "/fujp/lua_display.lua"
require "/scripts/util.lua"

function build(directory, config, parameters, level, seed)
	if not parameters.stemName then
		-- a pine tree isn't PERFECTLY generic but it's close enough
		parameters.stemName = "pineytree"
		parameters.foliageName = parameters.foliageName or "pinefoliage"
	end
	config.inventoryIcon = jarray()

	table.insert(config.inventoryIcon, {
			image = string.format("%s?hueshift=%s", util.absolutePath(root.treeStemDirectory(parameters.stemName), "saplingicon.png"), parameters.stemHueShift or 0)
		})

	if parameters.foliageName then
		table.insert(config.inventoryIcon, {
				image = string.format("%s?hueshift=%s", util.absolutePath(root.treeFoliageDirectory(parameters.foliageName), "saplingicon.png"), parameters.foliageHueShift or 0)
			})
	end

	-- begin added code

	saplings=root.assetJson("/items/buildscripts/buildsaplingfu.config")

	local stemName=saplings.stem[parameters.stemName]
	local foliageName=saplings.foliage[parameters.foliageName]

	if foliageName == "" then foliageName = nil end
	if stemName == "" then stemName = nil end

	parameters.shortdescription=""..(stemName or "不明")

	parameters.shortdescription=parameters.shortdescription..((foliageName and " "..foliageName) or "")

	parameters.shortdescription=parameters.shortdescription.."の苗木"

	parameters.description = "^green;葉^reset;："..(foliageName or "不明").."（色相："..math.floor(math.abs(parameters.foliageHueShift or 0))..")\n^orange;幹^reset;："..(stemName or "不明").."（色相："..math.floor(math.abs(parameters.stemHueShift or 0))..")"

	-- end added code

	return config, parameters
end

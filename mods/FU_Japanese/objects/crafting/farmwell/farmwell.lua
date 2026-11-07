function init()
	object.setInteractive(true)
end

function update(dt)
	object.setInteractive(true)
	if storage.waterCount == nil then
		storage.waterCount = 0
	end

	if (not (world.type() == 'playerstation')) and (not (world.type == 'unknown')) then
		storage.waterCount = storage.waterCount + dt
	end
end

function onInteraction(args)
	if not storage.waterCount then
	 storage.waterCount = 0
	end

	if storage.waterCount and storage.waterCount > 600 then
		storage.waterCount = 600
	end
	if storage.waterCount and storage.waterCount > 99 then
		local p = object.position()
		world.spawnItem("liquidwater", p, 10)
		storage.waterCount = storage.waterCount - 100
	end
	if storage.waterCount < 100 then
		object.say("水量："..math.ceil(storage.waterCount).."（ほぼ枯渇）")
	elseif storage.waterCount > 600 then
		object.say("水量："..math.ceil(storage.waterCount).."（あふれそう）")
	elseif storage.waterCount > 500 then
		object.say("水量："..math.ceil(storage.waterCount).."（満水）")
	elseif storage.waterCount > 400 then
		object.say("水量："..math.ceil(storage.waterCount).."（潤沢）")
	elseif storage.waterCount > 300 then
		object.say("水量："..math.ceil(storage.waterCount).."（十分）")
	elseif storage.waterCount > 200 then
		object.say("水量："..math.ceil(storage.waterCount).."（少量）")
	elseif storage.waterCount > 100 then
		object.say("水量："..math.ceil(storage.waterCount).."（残りわずか）")
	end
end

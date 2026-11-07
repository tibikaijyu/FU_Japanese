function fu_toggleAtmosphereMode()
	local text
	if player.worldId() ~= player.ownShipWorldId() then
		text = "大気判定の方式を切り替えられるのは船の所有者だけです。"
	elseif world.getProperty("ship.level") ~= 0 then
		text = "この機能は自由建造船専用です。"
	elseif world.getProperty("fu_byos.newAtmosphereSystem") then
		world.setProperty("fu_byos.newAtmosphereSystem", false)
		text = "自由建造船の大気判定を、プレイヤーの背後に背景壁があるかだけを調べる方式に変更しました。"
	else
		world.setProperty("fu_byos.newAtmosphereSystem", true)
		text = "自由建造船の大気判定を、プレイヤーが密閉された部屋にいるかを調べる方式に変更しました（開発中）。"
	end
	resetGUI()
	textTyper.init(cfg.TextData, text)
end

function fu_configureShipPet()
	local shipPet = world.getObjectParameter(pane.sourceEntity(), "shipPetType")
	if not shipPet then
		text = "この機能は、ペットがいるSAILでのみ使用できます。"
		resetGUI()
		textTyper.init(cfg.TextData, text)
		return
	end

	local petConfigPane = root.assetJson("/interface/objectcrafting/fu_pethouse/fu_pethouse.config")
	if petConfigPane and petConfigPane.gui then
		petConfigPane.gui.itemGrid = nil
		petConfigPane.gui.changeObjectPet = nil
		petConfigPane.gui.addObjectPetToList = nil
		petConfigPane.containerId = pane.sourceEntity()
		player.interact("ScriptPane", petConfigPane)
	end
end

function fu_crashberry()
	status.clearAllPersistentEffects()
	status.clearEphemeralEffects()
end

function fu_recheckresearch()
	player.setProperty("fu_recheckResearch",true)
end

function init()
	self.sounds = config.getParameter("sounds")
	self.colors = config.getParameter("colors")

	self.write = 0
end

function update(dt)
	if not world.sendEntityMessage(player.id(), "holdingNotepad"):result() then
		pane.dismiss()
	end
	if self.write > 0 then
		self.write = self.write - 1
	end
end

function writeSound()
	if self.write == 0 then
		self.write = 30
		pane.playSound(self.sounds.write, 0, 0.35)
	end
end

function makeAndSpawnNote()
	local text = widget.getText("writebox")
	local color = widget.getSelectedOption("colorpicker")
	local note = root.createItem("stickynote" .. self.colors[color])
	text = text:gsub("^%s*(.-)%s*$", "%1") -- strip leading/trailing whitespace
	if text == "" then
		note.parameters.description = "はがす前に何か書いておくべきだったかも…"
		note.parameters.floranDescription = "フローラン、はがすのが楽しーい。"
		note.parameters.glitchDescription = "困惑。何も書かずにはがすとは、何を考えていたのだろう？"
		note.parameters.novakidDescription = "あー、しまった。何か書くのを忘れちまったか？"
	else
		note.parameters.description = "書いてある内容：'" .. text .. "'"
		note.parameters.floranDescription = "メモに書いてあるー：'" .. text .. "'"
		note.parameters.glitchDescription = "備忘。'" .. text .. "'"
		note.parameters.novakidDescription = "書いてある内容：'" .. text .. "'"
	end
	oldNoteCount = player.hasCountOfItem(note, true)
	player.giveItem(note)
	if player.hasCountOfItem(note, true) > oldNoteCount then
		pane.playSound(self.sounds.peel, 0, 1.5)
		world.sendEntityMessage(player.id(), "consumeNote")
	else
		local e = "Error creating stickynote with parameters:/n/n"
		for k,v in pairs(note.parameters) do
			e = e .. "  " .. tostring(k) .. " : " .. tostring(v) .. "/n"
		end
		e = e .. "/n  inputText : " .. text .. "/n  inputColor : " .. color
		sb.logError(e)
	end
end
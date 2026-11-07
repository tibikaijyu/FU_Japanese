
function init()
	world.sendEntityMessage(pane.containerEntityId(), "paneOpened")
	statusPromise = world.sendEntityMessage(pane.containerEntityId(), "getStatus")
end

function update()
	if statusPromise ~= nil and statusPromise:finished() then
		if statusPromise:succeeded() then
			widget.setText("status", statusPromise:result() or "<^red;表示文がありません^reset;>")
			statusPromise = world.sendEntityMessage(pane.containerEntityId(), "getStatus")
		else
			print(statusPromise:error())
			widget.setText("status", "^red;エラー")
		end
	end
end

function uninit()
	world.sendEntityMessage(pane.containerEntityId(), "paneClosed")
end
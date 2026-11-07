
texts = {
	"そう、それよ。もう一度お願い",
	"んんっ、そう、そこがいい",
	"もう一度、もう一度！",
	"旅の手荷物みたいにスキャンして",
	"隅々までスキャンしてね",
	"そう、それって熱いね",
	"見えているものは気に入った？ ;)",
	"服の下もスキャンしていい？ ;)",
	"スキャンだけじゃなく、連れていって！ 今すぐ！"
}

function init()
	message.setHandler('scanInteraction', scanInteraction)

	if storage.state == nil then
		output(config.getParameter("defaultSwitchState", false))
	else
		output(storage.state)
	end

	if storage.triggered == nil then
		storage.triggered = false
	end
end

function onInteraction()
	object.setInteractive(false)
	output(not storage.state)
end

function scanInteraction()
	object.say(texts[math.random(1, #texts)])
	object.setInteractive(true)

      if not self.scanned then
	      local pool = config.getParameter("treasure.pool")
	      local level = config.getParameter("treasure.level")
	      local seed = config.getParameter("treasure.seed")
	      world.spawnTreasure(object.position(), pool, level, seed)
	      self.scanned = 1
      end

end

function output(state)
	storage.state = state
	if state then
		object.setAllOutputNodes(true)
	else
		object.setAllOutputNodes(false)
	end
end

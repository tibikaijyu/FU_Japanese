
function zb_sailInfo()
	resetGUI()
	local text = "新しいSAIL画面へようこそ！ 見た目の変更に加え、次の機能が利用できます：\n\n > 標準以外の通貨を表示できます（所持品画面にはゲーム本体の制限があるため表示できません）\n\n > ミッションをメインとサブのタブに分け、再挑戦も区別して表示します\n\n > 独自の機能を簡単に追加でき、『その他』メニューのボタンから呼び出せます（ZtarboundのMODページに手順があります）\n\n > Scripted SAILに完全対応しています。\n\n ご注意：乗組員やミッションの一部が表示されない場合は、『その他』の機能からいつでも標準のSAIL画面に戻れます。"
	textTyper.init(cfg.TextData, text)
end

function zb_skipStarterCrap()
	-- luacheck: ignore 511
	if false then--disabling this function until someone can make it not cause issues.
		local quests = {"gaterepair", "shiprepair", "human_mission1", "mechunlock", "outpostclue"}
		local str = "クエストID："

		for _, quest in ipairs(quests) do
			if not player.hasCompletedQuest(quest) then
				player.startQuest(quest)
				str = str.."\n"..quest
			end
		end
	end
	resetGUI()
	textTyper.init(cfg.TextData, "[(instant)"..str.."]")
end

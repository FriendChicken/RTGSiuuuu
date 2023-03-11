@echo off
if %1==add (
	if [%2] == [] (
		echo [ERROR] Not specifying the name of the trader you want to add
		exit /B
	)
	if not exist Traders\%2.py copy Templates\TRADER.py Traders\%2.py
	copy Templates\TRADER.json TradersJSON\%2.json
	jq-win64 ".TeamName = \"%2\"" Templates\TRADER.json >TradersJSON\%2.json
	copy RTG\exchange.json RTG\exchange.json.tmp
	jq-win64 ".Traders += {\"%2\": \"secret\"}" RTG\exchange.json.tmp >RTG\exchange.json
	del RTG\exchange.json.tmp
	echo Complete adding Trader: %2
	exit /B
)
if %1==del (
	if exist Traders\%2.py del Traders\%2.py
	if exist TradersJSON\%2.json del TradersJSON\%2.json
	copy RTG\exchange.json RTG\exchange.json.tmp
	jq-win64 "del(.Traders.%2)" RTG\exchange.json.tmp >RTG\exchange.json
	del RTG\exchange.json.tmp
	echo Completely deleted Trader: %2
	exit /B
)
if %1==change (
	if [%3] == [] (
		echo [ERROR] Not specifying the name of the trader you are changing to
		exit /B
	)
	if not exist Traders\%2.py (
		echo "[ERROR] No file named %2.py"
		exit /B
	)
	ren Traders\%2.py %3.py
	del TradersJSON\%2.json
	copy Templates\TRADER.json TradersJSON\%3.json
	jq-win64 ".TeamName = \"%3\"" Templates\TRADER.json >TradersJSON\%3.json
	copy RTG\exchange.json RTG\exchange.json.tmp
	jq-win64 "del(.Traders.%2)" RTG\exchange.json.tmp >RTG\exchange.json
	copy RTG\exchange.json RTG\exchange.json.tmp
	jq-win64 ".Traders += {\"%3\": \"secret\"}" RTG\exchange.json.tmp >RTG\exchange.json
	del RTG\exchange.json.tmp
	echo Complete changing Trader name from: %2 to: %3
	exit /B
)
if %1==run (
	goto runline
	
)
if %1==set (
	if %2==match (
		if [%3]==[] (
			echo [ERROR] Not specifying the name of the match
			exit /B
		)
		copy RTG\exchange.json RTG\exchange.json.tmp
		jq-win64 ".Engine.MatchEventsFile = \"Matches/%3/match_events.csv\"" RTG\exchange.json.tmp >RTG\exchange.json
		copy RTG\exchange.json RTG\exchange.json.tmp
		jq-win64 ".Engine.ScoreBoardFile = \"Matches/%3/score_board.csv\"" RTG\exchange.json.tmp >RTG\exchange.json
		del RTG\exchange.json.tmp
		if not exist ".\Matches\%3\" mkdir .\Matches\%3\
		echo Complete setting Match name to: %3
		exit /B
	)
	if %2==data (
		if [%3]==[] (
			echo [ERROR] Not specifying the number of the data
			exit /B
		)
		copy RTG\exchange.json RTG\exchange.json.tmp
		jq-win64 ".Engine.MarketDataFile = \"data/market_data%3.csv\"" RTG\exchange.json.tmp >RTG\exchange.json
		del RTG\exchange.json.tmp
		echo Complete setting the number of data to: %3
		exit /B
	)
REM	if %2==speed (
REM		if [%3]==[] (
REM			echo [ERROR] Not specifying the number of the speed
REM			exit /B
REM		)
REM		copy RTG\exchange.json RTG\exchange.json.tmp
REM		jq-win64 ".Engine.Speed = %3" RTG\exchange.json.tmp >RTG\exchange.json
REM		del RTG\exchange.json.tmp
REM		echo Complete setting the speed to: %3
REM		exit /B
REM	)
	echo [ERROR] No command in "set" called "%2"
	exit /B
)
if %1==get (
	if %2==match (
		FOR /F "tokens=*" %%g IN ('jq-win64 -r ".Engine.MatchEventsFile" RTG\exchange.json') DO (set _MatchName=%%g)
		echo Match name is: %_MatchName:~8,-17%
		exit /B
	)
	if %2==data (
		FOR /F "tokens=*" %%g IN ('jq-win64 -r ".Engine.MarketDataFile" RTG\exchange.json') DO (set _DataNum=%%g)
		echo Data number is: %_DataNum:~16,-4%
		exit /B
	)
REM	if %2==speed (
REM		FOR /F "tokens=*" %%g IN ('jq-win64 -r ".Engine.Speed" RTG\exchange.json') DO (set _Exchange_Speed=%%g)
REM		echo Speed is: %_Exchange_Speed%
REM		exit /B
REM	)
	echo [ERROR] No command in "get" called "%2"
	exit /B
)
if %1==reset (
	if %2==all (
		echo Have not done this part yet hahahahahahaha
		echo Reset complete
		exit /B
	)
	echo [ERROR] No command in "reset" called "%2"
	exit /B
)
echo [ERROR] No command called "%1"
exit /B
:runline
	copy .\Traders\* .\RTG
	copy .\TradersJSON\* .\RTG
	cd .\RTG
	if [%2]==[] (
		echo [ERROR] Not specifying the name of the traders
		cd ..
		exit /B
	)
	echo %*
	set "_tail=%*"
	echo %_tail%
	call set _tail=%%_tail:*%1=%%
	echo %_tail%
	setlocal EnableDelayedExpansion
	set "_out="
	echo !_out!
	for %%x in (%_tail%) do (
      	call set "_out=%%_out%% %%~x.py"
	)
	echo !_out!
	copy exchange.json exchange.json.tmp
	jq-win64 ".Engine.ScoreBoardFile = .Engine.ScoreBoardFile" exchange.json.tmp >exchange.json
	del exchange.json.tmp
	CALL ExchangeRenew.bat
	echo on
	python rtg.py run %_out%
	@echo off
	cd..
	exit /B
	




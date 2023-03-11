	@echo off
	setlocal disableDelayedExpansion
	set InputFile=exchange.json
	set OutputFile=exchange.json.tmp
	set "_strFind=    "MarketOpenDelay^": 5,"
	set "_strInsert=    "MarketOpenDelay^": 5.0,"
	set "_strFind2=    "Speed^": 1,"
	set "_strInsert2=    "Speed^": 1.0,"
	set "_strFind3=    "TickSize^": 1"
	set "_strInsert3=    "TickSize^": 1.00"
	set "_strFind4=    "MessageFrequencyInterval^": 1,"
	set "_strInsert4=    "MessageFrequencyInterval^": 1.0,"
	>"%OutputFile%" (
		for /f "tokens=* usebackq delims=" %%A in (%InputFile%) do (
			if ["%%A"] equ ["%_strFind%"] (
				echo %_strInsert%
			) else (
				if ["%%A"] equ ["%_strFind2%"] (
					echo %_strInsert2%
				) else (
					if ["%%A"] equ ["%_strFind3%"] (
						echo %_strInsert3%
					) else (
						if ["%%A"] equ ["%_strFind4%"] (
							echo %_strInsert4%
						) else (
							echo %%A
						)
					)
				)
			)
		)
	)
REM	del exchange.json
	copy exchange.json.tmp exchange.json
REM	del exchange.json.tmp
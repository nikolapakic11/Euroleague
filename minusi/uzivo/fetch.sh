for g in "$@"; do curl -s -H "User-Agent: curl/8.5.0" "https://live.euroleague.net/api/Boxscore?gamecode=$g&seasoncode=E2026" -o bs_$g.json; done

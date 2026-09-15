# Nightcap next steps

Updated 2026-09-15. The current issue disposition and publication boundaries are
in [the GitHub review](audits/github-issues-20260914.md).

1. The [#16 live audit](audits/aa-titles-20260915/README.md) found affected saved
   ownership. Preserve system/owned AAs; review the two unnamed Paladin rank
   owners and prerequisite dependents before disablement or client-string work.
2. #22: inspect bag inventory and economy before proposing a concrete price ladder.
3. #23: review the existing player-facing page, enable GitHub Pages and verify
   the deployed tabs. A committed index.html is not a deployed site.
4. #19/#20: capture Bard movement/song behavior in game before changing formulas.
5. Follow the existing multiclass/launcher plan for #10/#13–15/#36/#38/#39;
   #37 needs runtime rule validation and level-1 AA XP QA. #11 retains unresolved
   original acceptance details. #4 needs the column-versus-label decision.
6. #17 PoK routing, #26 augments and #32 waypoints retain their separate candidate,
   design and release gates. Do not infer deployment from local code.

Branch flow remains feature -> dev -> test (explicit in-game QA) -> main (owner
sign-off). The local main containing AA/balance candidates is not a license to
publish or deploy those candidates as accepted. Preserve the existing branches;
see the review for the exact published-main and accepted-DLL source commits.

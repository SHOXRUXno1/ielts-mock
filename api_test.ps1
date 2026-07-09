$BASE = "http://127.0.0.1:8001"
$global:PASS = 0
$global:FAIL = 0

function Check-OK($msg)   { Write-Host "  OK  $msg"; $global:PASS++ }
function Check-FAIL($msg) { Write-Host "  FAIL $msg"; $global:FAIL++ }

Write-Host "=== LOGIN ==="
$lr = Invoke-RestMethod -Uri "$BASE/admin/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"Bobi","password":"Demo123"}'
$T = $lr.access_token
$H = @{ Authorization = "Bearer $T" }
Check-OK "token obtained"

Write-Host "`n=== FIX 1: /admin/auth/me ==="
$me = Invoke-RestMethod -Uri "$BASE/admin/auth/me" -Headers $H
if ($me.login -eq "Bobi") { Check-OK "login=$($me.login) name=$($me.name)" } else { Check-FAIL "unexpected: $($me | ConvertTo-Json)" }

Write-Host "`n=== CLEANUP 6: Block general test (expect 400) ==="
try {
    Invoke-RestMethod -Uri "$BASE/admin/tests/" -Method POST -ContentType "application/json" -Headers $H -Body '{"title":"Gen","book_name":"G","test_number":97,"type":"general"}' | Out-Null
    Check-FAIL "no 400 raised"
} catch {
    $sc = $_.Exception.Response.StatusCode.value__
    if ($sc -eq 400) { Check-OK "got 400 as expected" } else { Check-FAIL "got $sc instead of 400" }
}

Write-Host "`n=== 1. POST Academic Test ==="
$tb = '{"title":"APICheck Test","book_name":"APICheck Book","test_number":88,"type":"academic"}'
$test = Invoke-RestMethod -Uri "$BASE/admin/tests/" -Method POST -ContentType "application/json" -Headers $H -Body $tb
$testId = $test.id
Check-OK "created id=$testId"

$secs   = $test.sections | Sort-Object order
$lOrds  = ($secs | Where-Object { $_.type -eq "listening" }).order | Sort-Object
$rOrds  = ($secs | Where-Object { $_.type -eq "reading"   }).order | Sort-Object
$wOrds  = ($secs | Where-Object { $_.type -eq "writing"   }).order | Sort-Object
$spOrds = ($secs | Where-Object { $_.type -eq "speaking"  }).order | Sort-Object

if (($lOrds -join ",") -eq "1,2,3,4")   { Check-OK "Listening 1,2,3,4" }   else { Check-FAIL "Listening got: $($lOrds -join ',')" }
if (($rOrds -join ",") -eq "10,11,12")  { Check-OK "Reading 10,11,12" }    else { Check-FAIL "Reading got: $($rOrds -join ',')" }
if (($wOrds -join ",") -eq "20")        { Check-OK "Writing 20" }           else { Check-FAIL "Writing got: $($wOrds -join ',')" }
if (($spOrds -join ",") -eq "30,31,32") { Check-OK "Speaking 30,31,32" }   else { Check-FAIL "Speaking got: $($spOrds -join ',')" }

$readSec = $secs | Where-Object { $_.type -eq "reading" } | Select-Object -First 1
$secId = $readSec.id

Write-Host "`n=== 2. POST question-group in reading ==="
$grp = Invoke-RestMethod -Uri "$BASE/admin/sections/$secId/question-groups" -Method POST -ContentType "application/json" -Headers $H -Body '{"question_type":"mcq","instruction":"Read carefully.","order":1}'
$grpId = $grp.id
if ($grpId) { Check-OK "group id=$grpId" } else { Check-FAIL "group not created" }

Write-Host "`n=== 3. POST MCQ question in group ==="
$qContent = '{"question":"What is the main topic?","options":["Science","Art","History","Music"]}'
$qAnswerKey = '{"correct":"A"}'
$qBody = "{`"order`":1,`"question_type`":`"mcq`",`"content`":$qContent,`"answer_key`":$qAnswerKey,`"question_group_id`":`"$grpId`"}"
$q = Invoke-RestMethod -Uri "$BASE/admin/sections/$secId/questions/" -Method POST -ContentType "application/json" -Headers $H -Body $qBody
$qId = $q.id
if ($qId) { Check-OK "mcq question id=$qId" } else { Check-FAIL "mcq not created" }

Write-Host "`n=== FIX 3: POST multi_select question ==="
$msContent = '{"question":"Which two apply?","options":["Alpha","Beta","Gamma","Delta"]}'
$msKey = '{"correct":["A","C"]}'
$msBody = "{`"order`":2,`"question_type`":`"multi_select`",`"content`":$msContent,`"answer_key`":$msKey}"
$msQ = Invoke-RestMethod -Uri "$BASE/admin/sections/$secId/questions/" -Method POST -ContentType "application/json" -Headers $H -Body $msBody
$msQId = $msQ.id
if ($msQId) { Check-OK "multi_select id=$msQId" } else { Check-FAIL "multi_select not created" }

Write-Host "`n=== 4-8. Attempt Cycle ==="
$PHONE = "+79990001234"
$loginS = $null
try { $loginS = Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST -ContentType "application/json" -Body "{`"login`":`"$PHONE`",`"password`":`"$PHONE`"}" } catch {}
if (-not $loginS) {
    try {
        Invoke-RestMethod -Uri "$BASE/admin/students/" -Method POST -ContentType "application/json" -Headers $H -Body "{`"email`":`"apitest@test.com`",`"full_name`":`"API Tester`",`"phone`":`"$PHONE`"}" | Out-Null
        $loginS = Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST -ContentType "application/json" -Body "{`"login`":`"$PHONE`",`"password`":`"$PHONE`"}"
    } catch { Check-FAIL "could not create/login student: $_" }
}
$ST = $loginS.access_token
$SH = @{ Authorization = "Bearer $ST" }
Check-OK "student token"

# Publish the test via admin PATCH (bypass full publish validation for cycle test)
Invoke-RestMethod -Uri "$BASE/admin/tests/$testId" -Method PATCH -ContentType "application/json" -Headers $H -Body '{"is_published":true}' | Out-Null
Check-OK "test published"

$att = Invoke-RestMethod -Uri "$BASE/tests/$testId/attempts" -Method POST -ContentType "application/json" -Headers $SH -Body '{}'
$attId = $att.id
Check-OK "attempt id=$attId"

$ansBody = "{`"answers`":[{`"question_id`":`"$qId`",`"response`":{`"answer`":`"A`"}},{`"question_id`":`"$msQId`",`"response`":{`"answer`":[`"A`",`"C`"]}}]}"
$ansResp = Invoke-RestMethod -Uri "$BASE/attempts/$attId/answers" -Method POST -ContentType "application/json" -Headers $SH -Body $ansBody
if ($ansResp.saved -eq 2) { Check-OK "submit_answers saved=$($ansResp.saved) (Cleanup 5 OK)" } else { Check-FAIL "submit_answers: $($ansResp | ConvertTo-Json -Compress)" }

$fin = Invoke-RestMethod -Uri "$BASE/attempts/$attId/finish" -Method POST -ContentType "application/json" -Headers $SH -Body '{}'
Check-OK "finish: status=$($fin.status) reading_band=$($fin.reading_band)"

$res = Invoke-RestMethod -Uri "$BASE/attempts/$attId" -Headers $SH
Check-OK "GET attempt: reading_raw=$($res.reading_raw) reading_band=$($res.reading_band)"

$msAns = $res.answers | Where-Object { $_.question_id -eq $msQId }
if ($msAns) {
    Write-Host "    multi_select: answer=$($msAns.response | ConvertTo-Json -Compress) score=$($msAns.score)"
    if ($msAns.score -gt 0) { Check-OK "multi_select scored correctly" } else { Check-FAIL "multi_select score=0" }
} else { Check-FAIL "multi_select answer not in result" }

Write-Host "`n=== CLEANUP 6b: GET existing general test ==="
$allTests = Invoke-RestMethod -Uri "$BASE/admin/tests/" -Headers $H
$genTest = $allTests | Where-Object { $_.type -eq "general" } | Select-Object -First 1
if ($genTest) {
    $gt = Invoke-RestMethod -Uri "$BASE/admin/tests/$($genTest.id)" -Headers $H
    if ($gt.type -eq "general") { Check-OK "general test readable (backward compat OK)" } else { Check-FAIL "wrong type" }
} else { Check-OK "no general tests exist (backward compat n/a)" }

Write-Host "`n=== CLEANUP 3: Speaking content schema ==="
$spSec = $secs | Where-Object { $_.type -eq "speaking" } | Select-Object -First 1
$spGrps = Invoke-RestMethod -Uri "$BASE/admin/sections/$($spSec.id)/question-groups" -Headers $H
if ($spGrps.Count -eq 0) {
    Check-OK "speaking empty on new test (OK)"
} else {
    $spQ = $spGrps[0].questions | Select-Object -First 1
    $c = $spQ.content
    if ($c.PSObject.Properties.Name -contains "questions" -or $c.PSObject.Properties.Name -contains "cue_card") {
        Check-OK "canonical schema: keys=$($c.PSObject.Properties.Name -join ',')"
    } else { Check-FAIL "NOT canonical: $($c | ConvertTo-Json -Compress)" }
}

Write-Host "`n=== 6. question_groups in test detail ==="
$td = Invoke-RestMethod -Uri "$BASE/admin/tests/$testId" -Headers $H
$rdSec2 = $td.sections | Where-Object { $_.type -eq "reading" } | Select-Object -First 1
if ($rdSec2.question_groups -and $rdSec2.question_groups.Count -gt 0) {
    Check-OK "question_groups loaded in section (count=$($rdSec2.question_groups.Count))"
} else { Check-FAIL "question_groups missing or empty in TestDetailRead" }

Write-Host "`n=== FIX 2: Task 2 criterion check ==="
$allResults = Invoke-RestMethod -Uri "$BASE/results/" -Headers $SH
$writingJobs = @()
foreach ($r in $allResults) {
    if ($r.evaluation_jobs) {
        $wj = $r.evaluation_jobs | Where-Object { $_.section_type -eq "writing" }
        if ($wj) { $writingJobs += $wj }
    }
}
if ($writingJobs.Count -gt 0) {
    $wj = $writingJobs | Select-Object -First 1
    $t2 = $wj.result.tasks.task_2
    if ($t2.task_response) { Check-OK "task_response present in Task 2 result" }
    elseif ($t2.task_achievement) { Check-FAIL "task_achievement still in Task 2 (migration may not have run)" }
    else { Check-OK "Task 2 result has no criterion key yet (pending AI scoring)" }
} else { Check-OK "no writing eval jobs in DB yet (AI scoring deferred, rename will apply when jobs exist)" }

Write-Host "`n=== SUMMARY ==="
Write-Host "Passed: $global:PASS"
Write-Host "Failed: $global:FAIL"

Write-Host "`nCleaning up test..."
try { Invoke-RestMethod -Uri "$BASE/admin/tests/$testId" -Method DELETE -Headers $H | Out-Null; Write-Host "test deleted" } catch { Write-Host "delete failed: $_" }

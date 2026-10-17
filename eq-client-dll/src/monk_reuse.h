#pragma once

namespace nightcap { namespace client_ui {
// SkillManager has only two shared combat timers. Keep six owned records, and
// exchange the relevant native player slot only while its submitter executes.
// Native targeting, duration calculation, haste and packet generation survive.
struct MonkReuse { DWORD started=0, duration=0; BYTE ready=1; };
static MonkReuse monk_reuse[6];
inline int MonkReuseIndex(int skill) {
    switch(skill) {
    case 21: return 0; // Dragon Punch / Tail Rake
    case 23: return 1; // Eagle Strike
    case 26: return 2; // Flying Kick
    case 30: return 3; // Kick
    case 38: return 4; // Round Kick
    case 52: return 5; // Tiger Claw
    default: return -1;
    }
}
inline void ResetMonkReuse() { for(auto& timer:monk_reuse) timer=MonkReuse{}; }
inline MonkReuse* IndependentMonkReuse(int skill) {
    const int index=MonkReuseIndex(skill);
    return index>=0 && CurrentIdentity() && (state.ClassMask() & (1u<<6)) ? &monk_reuse[index] : nullptr;
}
using SkillReuseSet=void(__thiscall*)(void*,int,DWORD);
using SkillReuseGet=DWORD(__thiscall*)(void*,int);
using SkillReuseReady=BYTE(__thiscall*)(void*,int);
using AdjustCombatReuse=DWORD(__thiscall*)(void*,DWORD,int);
static SkillReuseSet original_reuse_start=nullptr,original_reuse_duration=nullptr,original_reuse_begin=nullptr;
static SkillReuseGet original_reuse_get_start=nullptr,original_reuse_get_duration=nullptr;
static SkillReuseReady original_reuse_ready=nullptr;
static AdjustCombatReuse adjust_combat_reuse=nullptr;
using SubmitCombatAttack=BYTE(__thiscall*)(void*,int,int,void*);
static SubmitCombatAttack original_combat_submit=nullptr;
inline void __fastcall MonkReuseStart(void* self,void*,int skill,DWORD value) {
    if(auto* timer=IndependentMonkReuse(skill)) timer->started=value;
    else original_reuse_start(self,skill,value);
}
inline DWORD __fastcall MonkReuseGetStart(void* self,void*,int skill) {
    if(auto* timer=IndependentMonkReuse(skill)) return timer->started;
    return original_reuse_get_start(self,skill);
}
inline void __fastcall MonkReuseDuration(void* self,void*,int skill,DWORD value) {
    if(auto* timer=IndependentMonkReuse(skill)) timer->duration=value;
    else original_reuse_duration(self,skill,value);
}
inline DWORD __fastcall MonkReuseGetDuration(void* self,void*,int skill) {
    if(auto* timer=IndependentMonkReuse(skill)) {
        // Same receiver and arguments as stock SkillManager::GetReuseDuration.
        const auto character=*reinterpret_cast<BYTE**>(base+0x9D261C);
        return adjust_combat_reuse(*reinterpret_cast<void**>(character+0x2DD0),timer->duration,0);
    }
    return original_reuse_get_duration(self,skill);
}
inline void __fastcall MonkReuseBegin(void* self,void*,int skill,DWORD value) {
    if(auto* timer=IndependentMonkReuse(skill)) {
        timer->ready=static_cast<BYTE>(value);
        if(timer->ready) timer->duration=0;
    } else original_reuse_begin(self,skill,value);
}
inline BYTE __fastcall MonkReuseIsReady(void* self,void*,int skill) {
    if(auto* timer=IndependentMonkReuse(skill)) return timer->ready;
    return original_reuse_ready(self,skill);
}
struct MonkReuseScope {
    MonkReuse* timer;
    DWORD* player_duration;
    DWORD* player_started;
    DWORD saved_duration,saved_started;
};
inline void BeginMonkReuseScope(MonkReuseScope& scope,void* player,int skill) {
    scope.timer=IndependentMonkReuse(skill);
    if(!scope.timer) return;
    const unsigned index=skill==52 ? 1 : 0;
    scope.player_duration=reinterpret_cast<DWORD*>(static_cast<BYTE*>(player)+0x368+index*4);
    scope.player_started=reinterpret_cast<DWORD*>(static_cast<BYTE*>(player)+0x390+index*4);
    scope.saved_duration=*scope.player_duration;
    scope.saved_started=*scope.player_started;
    *scope.player_duration=scope.timer->duration;
    *scope.player_started=scope.timer->started;
}
inline void EndMonkReuseScope(MonkReuseScope& scope) {
    if(!scope.timer) return;
    scope.timer->duration=*scope.player_duration;
    scope.timer->started=*scope.player_started;
    *scope.player_duration=scope.saved_duration;
    *scope.player_started=scope.saved_started;
    scope.timer=nullptr;
}
inline BYTE __fastcall SubmitIndependentMonkAttack(void* player,void*,int attack,int skill,void* target) {
    MonkReuseScope scope={};
    BeginMonkReuseScope(scope,player,skill);
    BYTE submitted=0;
    __try {
        submitted=original_combat_submit(player,attack,skill,target);
        if(submitted && scope.timer) scope.timer->ready=0;
    } __finally {
        EndMonkReuseScope(scope);
    }
    return submitted;
}
inline void __fastcall CommitMonkReuseAfterSubmit(void* self,void*,int skill,DWORD value) {
    // The native caller reads the shared player slot after our submitter scope
    // restored it. The independent record already owns the captured timestamp.
    if(!IndependentMonkReuse(skill)) original_reuse_start(self,skill,value);
}
inline bool InstallMonkReuse() {
    if(!MatchSEH(base+kMonkReuseAdjustRva,kExpectedMonkReuseAdjust,base)) return false;
    adjust_combat_reuse=reinterpret_cast<AdjustCombatReuse>(base+kMonkReuseAdjustRva);
    original_reuse_start=reinterpret_cast<SkillReuseSet>(EntryHook(base+kMonkReuseStartRva,kExpectedMonkReuseStart,reinterpret_cast<void*>(&MonkReuseStart)));
    original_reuse_get_start=reinterpret_cast<SkillReuseGet>(EntryHook(base+kMonkReuseGetStartRva,kExpectedMonkReuseGetStart,reinterpret_cast<void*>(&MonkReuseGetStart)));
    original_reuse_duration=reinterpret_cast<SkillReuseSet>(EntryHook(base+kMonkReuseDurationRva,kExpectedMonkReuseDuration,reinterpret_cast<void*>(&MonkReuseDuration)));
    original_reuse_get_duration=reinterpret_cast<SkillReuseGet>(EntryHook(base+kMonkReuseGetDurationRva,kExpectedMonkReuseGetDuration,reinterpret_cast<void*>(&MonkReuseGetDuration)));
    original_reuse_begin=reinterpret_cast<SkillReuseSet>(EntryHook(base+kMonkReuseBeginRva,kExpectedMonkReuseBegin,reinterpret_cast<void*>(&MonkReuseBegin)));
    original_reuse_ready=reinterpret_cast<SkillReuseReady>(EntryHook(base+kMonkReuseReadyRva,kExpectedMonkReuseReady,reinterpret_cast<void*>(&MonkReuseIsReady)));
    original_combat_submit=reinterpret_cast<SubmitCombatAttack>(SEHEntryHook(base+kSpecialAttackSubmitRva,kExpectedSpecialAttackSubmit,reinterpret_cast<void*>(&SubmitIndependentMonkAttack),base));
    return original_reuse_start && original_reuse_get_start && original_reuse_duration &&
        original_reuse_get_duration && original_reuse_begin && original_reuse_ready && original_combat_submit;
}
} }

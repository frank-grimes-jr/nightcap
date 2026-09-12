#pragma once
#include "common/json/json.hpp"
class Client;
class Mob;
void NightcapBalanceStartClock();
nlohmann::json NightcapBalanceRuntimeProbe(Client *client);
bool NightcapBalanceRecordDeath(Mob *mob);
bool NightcapBalanceIsTerminal(Mob *mob);
nlohmann::json NightcapBalanceEncounter(Client *client, const nlohmann::json &input);
nlohmann::json NightcapBalanceClientCombatState(Client *client);

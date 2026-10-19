#pragma once
#include "common/json/json.hpp"
class Client;
class Mob;
void NightcapBalanceStartClock();
void NightcapBalanceCaptureAAPurchaseEvents();
nlohmann::json NightcapBalanceAAPurchaseEvents();
nlohmann::json NightcapBalanceRuntimeProbe(Client *client);
nlohmann::json NightcapBalanceAAProbe(Client *client, const nlohmann::json &input);
nlohmann::json NightcapBalancePetProbe(Client *client, const nlohmann::json &input);
bool NightcapBalanceRecordDeath(Mob *mob);
bool NightcapBalanceIsTerminal(Mob *mob);
nlohmann::json NightcapBalanceEncounter(Client *client, const nlohmann::json &input);
nlohmann::json NightcapBalanceClientCombatState(Client *client);
nlohmann::json NightcapBalanceClientLedger(Client *client);

void NightcapBalanceCaptureReleaseTransport();
void NightcapBalanceCaptureDisconnectEvents();
nlohmann::json NightcapBalanceDisconnectEvents();
void NightcapBalanceResetReleasePackets(Client *client);
nlohmann::json NightcapBalanceReleasePackets(Client *client);

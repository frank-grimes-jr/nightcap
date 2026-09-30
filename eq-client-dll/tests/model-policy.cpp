#include <cassert>
#include <iostream>
#include "../src/model_policy.h"

int main() {
    using namespace nightcap::models;
    const char* disabled[] = {nullptr, "", "FALSE", "0", "yes", "TRUEjunk", "2"};
    for (const char* value : disabled) assert(!ModernOptIn(value));
    for (const char* value : {"TRUE", "true", "True", "1"}) assert(ModernOptIn(value));
    assert(!strcmp(ClassicSetting("Defaults", "AllLuclinPcModelsOff", "eqclient.ini"), "TRUE"));
    assert(!strcmp(ClassicSetting("defaults", "useluclinelementals", "C:\\Game\\EQCLIENT.INI"), "FALSE"));
    assert(!strcmp(ClassicSetting("Defaults", "UseLuclinHumanMale", "eqclient.ini"), "FALSE"));
    assert(!strcmp(ClassicSetting("Defaults", "UseLuclinIksarFemale", "eqclient.ini"), "FALSE"));
    assert(!strcmp(ClassicSetting("Defaults", "UseLuclinVahShirMale", "eqclient.ini"), "FALSE"));
    for (const char* key : {"", "UseLuclin", "UseLuclinH", "UseLuclinHuman", "UseLuclinHumanMaleExtra", "UseLuclinSomethingElse", "WindowedMode", "UISkin"})
        assert(ClassicSetting("Defaults", key, "eqclient.ini") == nullptr);
    assert(ClassicSetting("Options", "UseLuclinElementals", "eqclient.ini") == nullptr);
    assert(ClassicSetting("Defaults", "UseLuclinElementals", "character.ini") == nullptr);
    assert(ClassicSetting(nullptr, nullptr, nullptr) == nullptr);
    char buffer[8] = "guard";
    assert(CopySetting("FALSE", buffer, sizeof(buffer)) == 5 && !strcmp(buffer, "FALSE"));
    assert(CopySetting("TRUE", buffer, 3) == 2 && !strcmp(buffer, "TR"));
    assert(CopySetting("TRUE", buffer, 1) == 0 && buffer[0] == 0);
    buffer[0] = 'x';
    assert(CopySetting("TRUE", buffer, 0) == 0 && buffer[0] == 'x');
    assert(CopySetting("TRUE", nullptr, 5) == 0);
    std::cout << "PASS: classic defaults, explicit opt-in, scope and profile buffer contract\n";
}

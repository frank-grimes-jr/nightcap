#include "common/item_data.h"
#include "common/spdat.h"
#include <cstddef>
#include <iostream>

int main()
{
	using Item = EQ::ItemData;
	std::cout << sizeof(Item) << ' ' << offsetof(Item, ID) << ' '
		<< offsetof(Item, CastTime_) << ' ' << offsetof(Item, MaxCharges) << ' '
		<< offsetof(Item, CastTime) << ' ' << offsetof(Item, Click) << ' '
		<< offsetof(Item, ClickName) << ' ' << sizeof(SPDat_Spell_Struct) << '\n';
}

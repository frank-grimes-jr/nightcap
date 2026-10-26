// Native custom-data methods retained verbatim for regression coverage.

// common/strings.cpp SHA256 c248497e5f5bb51858bb43772b94b5d4db13a11571d531e8185afc012a23ca31
std::vector<std::string> Strings::Split(const std::string &s, const std::string &delimiter)
{
	size_t                   pos_start = 0, pos_end, delim_len = delimiter.length();
	std::string              token;
	std::vector<std::string> res;

	while ((pos_end = s.find(delimiter, pos_start)) != std::string::npos) {
		token     = s.substr(pos_start, pos_end - pos_start);
		pos_start = pos_end + delim_len;
		res.push_back(token);
	}

	res.emplace_back(s.substr(pos_start));
	return res;
}

// common/item_instance.cpp SHA256 f8dec73c5b3f0c77e7e964a2e233efd35d3180b3dcc41d4cf1edebeda9b2b3b8
std::string EQ::ItemInstance::GetCustomDataString() const {
	std::string ret_val;
	auto iter = m_custom_data.begin();
	while (iter != m_custom_data.end()) {
		if (ret_val.length() > 0) {
			ret_val += "^";
		}
		ret_val += iter->first;
		ret_val += "^";
		ret_val += iter->second;
		++iter;

		if (ret_val.length() > 0) {
			ret_val += "^";
		}
	}
	return ret_val;
}

void EQ::ItemInstance::SetCustomDataString(const std::string& str)
{
	auto components = Strings::Split(str, "^");
	auto value_count = components.size() / 2;

	for (auto i = 0; i < value_count; i++) {
		auto identifier = components[i * 2];
		auto value = components[(i * 2) + 1];

		SetCustomData(identifier, value);
	}
}

void EQ::ItemInstance::SetCustomData(const std::string& identifier, const std::string& value) {
	DeleteCustomData(identifier);
	m_custom_data[identifier] = value;
}

void EQ::ItemInstance::DeleteCustomData(const std::string& identifier) {
	auto iter = m_custom_data.find(identifier);
	if (iter != m_custom_data.end()) {
		m_custom_data.erase(iter);
	}
}

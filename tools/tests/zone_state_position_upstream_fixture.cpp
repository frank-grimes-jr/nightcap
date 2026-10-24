// Exact retained waypoints.cpp helpers; full source SHA-256 recorded below.
// SendTo receiver renamed Mob to NPC to fit the narrow constructor fixture.
// AI_Start's final native lines call SendTo(GetX(), GetY(), GetZ()) then
// SaveGuardSpot(GetPosition()); the constructor fixture executes that sequence.
// SHA-256 8ecd6d584bbb5fbcddc2e87f1707daf7c74232653a0613c732d14328e6819fee
void NPC::SendTo(float new_x, float new_y, float new_z) {
	if (IsNPC()) {
		entity_list.ProcessMove(CastToNPC(), new_x, new_y, new_z);
	}

	m_Position.x = new_x;
	m_Position.y = new_y;
	m_Position.z = new_z;
	LogAIDetail("Sent To ({}, {}, {})", new_x, new_y, new_z);

	if (flymode == GravityBehavior::Flying)
		return;

	//fix up pathing Z, this shouldent be needed IF our waypoints
	//are corrected instead
	if (zone->HasMap() && RuleB(Map, FixPathingZOnSendTo))
	{
		if (!RuleB(Watermap, CheckForWaterOnSendTo) || !zone->HasWaterMap() ||
			(zone->HasWaterMap() && !zone->watermap->InWater(glm::vec3(m_Position))))
		{
			glm::vec3 dest(m_Position.x, m_Position.y, m_Position.z);

			float newz = zone->zonemap->FindBestZ(dest, nullptr);

			LogAIDetail("BestZ returned {} at {}, {}, {}", newz, m_Position.x, m_Position.y, m_Position.z);

			if ((newz > -2000) && std::abs(newz - dest.z) < RuleR(Map, FixPathingZMaxDeltaSendTo)) // Sanity check.
				m_Position.z = newz + 1;
		}
	}
	else
		m_Position.z += 0.1;
}

void NPC::SaveGuardSpot(const glm::vec4 &pos)
{
	m_GuardPoint = pos;

	if (m_GuardPoint.w == 0)
		m_GuardPoint.w = 0.0001;		//hack to make IsGuarding simpler
	LogAIDetail("Setting guard position to [{}]", to_string(static_cast<glm::vec3>(m_GuardPoint)));
}

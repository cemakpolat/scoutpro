import re

with open('frontend/src/components/ModelCenter.tsx', 'r') as f:
    content = f.read()

# 1. Import PlayerTrajectory
content = re.sub(
    r"import TaskQueue from '\./TaskQueue';",
    r"import TaskQueue from './TaskQueue';\nimport PlayerTrajectory from './PlayerTrajectory';",
    content
)

# 2. Add to ModelCenterTab
content = re.sub(
    r"\| 'batch'",
    r"| 'batch' | 'trajectory'",
    content
)

# 3. Add to AREA_CARDS under Player Assessment
content = re.sub(
    r"\{ label: 'Performance Tracker', tab: 'performance-tracker' \},",
    r"{ label: 'Performance Tracker', tab: 'performance-tracker' },\n      { label: 'Player Trajectory & Forecast', tab: 'trajectory' },",
    content
)

# 4. Add to sub-navigation
content = re.sub(
    r"\{ id: 'batch' as const, label: 'Batch Tasks', icon: ListChecks \},",
    r"{ id: 'batch' as const, label: 'Batch Tasks', icon: ListChecks },\n          { id: 'trajectory' as const, label: 'Player Trajectory', icon: Activity },",
    content
)

# 5. Append component before final closing div
replacement = """      {activeTab === 'trajectory' && (
        <div className="space-y-6">
          <PlayerTrajectory playerId={initialPlayerId} />
        </div>
      )}
    </div>
  );
};"""

content = re.sub(
    r"    </div>\n  \);\n};",
    replacement,
    content
)

with open('frontend/src/components/ModelCenter.tsx', 'w') as f:
    f.write(content)

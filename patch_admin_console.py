import re

with open('frontend/src/components/AdminConsole.tsx', 'r') as f:
    content = f.read()

# Add import for DataIngestionDashboard
content = re.sub(
    r"import \{ useApi \} from '../hooks/useApi';",
    r"import { useApi } from '../hooks/useApi';\nimport { DataIngestionDashboard } from './admin/DataIngestionDashboard';",
    content
)

# Add section
content = re.sub(
    r"\{ id: 'system', label: 'System Health', icon: Activity \},",
    r"{ id: 'system', label: 'System Health', icon: Activity },\n    { id: 'ingestion', label: 'Batch Data Manager', icon: Database },",
    content
)

# Render section
content = re.sub(
    r"\{activeSection === 'system' \&\& \(\s*<div className=\"bg-slate-800 rounded-xl p-6 text-center text-slate-400\">\s*System Health \& Performance Monitoring Dashboard\s*</div>\s*\)\}",
    r"{activeSection === 'system' && (\n        <div className=\"bg-slate-800 rounded-xl p-6 text-center text-slate-400\">\n          System Health & Performance Monitoring Dashboard\n        </div>\n      )}\n      {activeSection === 'ingestion' && (\n        <div className=\"rounded-xl\">\n          <DataIngestionDashboard />\n        </div>\n      )}",
    content
)

with open('frontend/src/components/AdminConsole.tsx', 'w') as f:
    f.write(content)

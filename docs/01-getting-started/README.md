# Getting Started with ScoutPro

Welcome to ScoutPro! This folder contains guides for getting the system up and running.

---

## 📚 Which Guide Should I Read?

### ✨ **Start Here (3 steps, 10 minutes)**
→ **[QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md)**

Three copy-paste commands to get running:
```bash
./manage.sh start    # Start all services
./manage.sh seed     # Load all data + compute statistics
# Access at http://localhost:5173
```

### 📖 **More Options & Details**
→ **[QUICK_START.md](QUICK_START.md)**

Different ways to start the system (dev mode, local, full Docker stack, etc.)

### 🔧 **Command Reference**
→ **[../03-development/MANAGE_COMMANDS.md](../03-development/MANAGE_COMMANDS.md)**

Complete reference for all `manage.sh` commands:
- `start` — Start services
- `stop` — Stop services  
- `seed` — Load data + compute statistics
- `clean` — Full reset
- `status` — Show system status
- And more...

### 📊 **Understanding Statistics**
→ **[../03-development/STATISTICS_OPERATIONS.md](../03-development/STATISTICS_OPERATIONS.md)**

Learn about:
- What statistics aggregation is
- When it runs (automatic during seeding)
- Available metrics (player stats, team stats)
- How to troubleshoot

### 🚀 **CI/CD & Automation**
→ **[../03-development/CICD_AUTOMATION.md](../03-development/CICD_AUTOMATION.md)**

Automate ScoutPro with:
- GitHub Actions
- GitLab CI
- Jenkins
- Docker/Kubernetes
- Custom scripts

### 📋 **Full Getting Started Guide**
→ **[GETTING_STARTED.md](GETTING_STARTED.md)**

Comprehensive guide with:
- Prerequisites
- All startup options
- Credentials
- First login
- Troubleshooting

---

## 🎯 Quick Decision Tree

| Question | Answer |
|----------|--------|
| **First time using ScoutPro?** | Read [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) |
| **Want to understand all options?** | Read [QUICK_START.md](QUICK_START.md) |
| **Need all management commands?** | Read [../03-development/MANAGE_COMMANDS.md](../03-development/MANAGE_COMMANDS.md) |
| **What is statistics aggregation?** | Read [../03-development/STATISTICS_OPERATIONS.md](../03-development/STATISTICS_OPERATIONS.md) |
| **Setting up CI/CD pipeline?** | Read [../03-development/CICD_AUTOMATION.md](../03-development/CICD_AUTOMATION.md) |
| **Having problems?** | See Troubleshooting in [GETTING_STARTED.md](GETTING_STARTED.md#10-common-troubleshooting) |

---

## ⚡ The Three Commands You Need to Know

```bash
# 1. Start the system
./manage.sh start

# 2. Load all data and compute statistics
./manage.sh seed

# 3. Check system status
./manage.sh status
```

That's it! Then access http://localhost:5173

---

## 🔑 Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| **App** | admin@scoutpro.com | admin123 |
| **MongoDB** | root | scoutpro123 |
| **Redis** | (none) | scoutpro123 |

---

## 🌐 Service URLs

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **API Gateway** | http://localhost:3001/api |
| **Kafka UI** | http://localhost:28090 |
| **MongoDB** | mongodb://localhost:27017 |

---

## 📊 Expected Data After Seeding

After running `./manage.sh seed`, you should have:

```
Teams:              18
Players:            571
Matches:            306
Match Events:       ~99,897
Player Statistics:  ~1,600
Team Statistics:    ~500
```

Use `./manage.sh status` to verify.

---

## 🆘 Quick Troubleshooting

### Services not starting?
```bash
./manage.sh status
```
Check which service failed and review its logs.

### Data not loading?
```bash
./manage.sh seed
```
Re-run the seed command. It's idempotent (safe to run multiple times).

### Need to start fresh?
```bash
./manage.sh clean  # ⚠️ Deletes all data
./manage.sh start
./manage.sh seed
```

### Frontend not responding?
```bash
./manage.sh stop
./manage.sh start
```

---

## 📚 Full Documentation Structure

```
docs/
├── 01-getting-started/          ← You are here
│   ├── QUICK_START_SIMPLE.md    ← Start here!
│   ├── QUICK_START.md
│   └── GETTING_STARTED.md       ← Full guide
├── 02-architecture/             ← System design
│   ├── OVERVIEW.md
│   └── ...
├── 03-development/              ← For developers
│   ├── MANAGE_COMMANDS.md        ← Command reference
│   ├── STATISTICS_OPERATIONS.md  ← Stats guide
│   ├── CICD_AUTOMATION.md        ← CI/CD setup
│   └── ...
└── 04-integration/              ← Frontend/backend integration
    └── ...
```

---

## ✅ Next Steps

1. **Read** [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) (5 min)
2. **Run** `./manage.sh start && ./manage.sh seed` (10 min)
3. **Open** http://localhost:5173 in your browser
4. **Log in** with admin@scoutpro.com / admin123
5. **Explore** the data!

---

## 🤝 Need Help?

- **Check** `./manage.sh status` for service health
- **View** `./manage.sh logs <service>` for error messages
- **Read** [GETTING_STARTED.md](GETTING_STARTED.md) for detailed troubleshooting
- **Review** [../02-architecture/OVERVIEW.md](../02-architecture/OVERVIEW.md) to understand the system

Happy scouting! ⚽

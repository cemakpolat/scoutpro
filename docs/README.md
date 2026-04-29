# ScoutPro Documentation

Welcome to the ScoutPro documentation! This guide will help you navigate all available documentation.

---

## 🚀 **Start Here**

| Document | Description | When to Use |
|----------|-------------|-------------|
| **[Quick Start](01-getting-started/QUICK_START.md)** | Get the system running in 5 minutes | First time setup |
| **[Current Status](07-status/CURRENT_STATUS.md)** | Honest assessment of what works | Before starting development |
| **[Architecture Overview](02-architecture/OVERVIEW.md)** | System architecture & design | Understanding the system |

---

## 📁 **Documentation Structure**

### **01 - Getting Started**
Get up and running quickly.

- **[QUICK_START.md](01-getting-started/QUICK_START.md)** - Step-by-step setup guide

### **02 - Architecture**
Understand how the system is designed.

- **[OVERVIEW.md](02-architecture/OVERVIEW.md)** - System architecture, services, data flow

### **03 - Development**
Guides for building features.

- **[IMPLEMENTATION_GUIDE.md](03-development/IMPLEMENTATION_GUIDE.md)** - How to implement new services

### **04 - Integration**
Connecting frontend and backend.

- **[FRONTEND_BACKEND_INTEGRATION.md](04-integration/FRONTEND_BACKEND_INTEGRATION.md)** - Integration guide

### **05 - Deployment**
_Coming soon - Deployment guides for Docker, Kubernetes, and Cloud_

### **06 - Operations**
_Coming soon - Monitoring, troubleshooting, and maintenance guides_

### **07 - Status**
Current state and roadmap.

- **[CURRENT_STATUS.md](07-status/CURRENT_STATUS.md)** - What's working, what's not
- **[ROADMAP.md](07-status/ROADMAP.md)** - Development roadmap and next steps

---

## 🎯 **Common Tasks**

### **I want to...**

**Get the system running**
→ [Quick Start Guide](01-getting-started/QUICK_START.md)

**Understand the architecture**
→ [Architecture Overview](02-architecture/OVERVIEW.md)

**Build a new service**
→ [Implementation Guide](03-development/IMPLEMENTATION_GUIDE.md)

**Connect frontend to backend**
→ [Integration Guide](04-integration/FRONTEND_BACKEND_INTEGRATION.md)

**Know what's working**
→ [Current Status](07-status/CURRENT_STATUS.md)

**See what's planned**
→ [Roadmap](07-status/ROADMAP.md)

**Fix common issues**
→ See "Troubleshooting" section in [Quick Start](01-getting-started/QUICK_START.md)

---

## 🔍 **Quick Reference**

### **Services & Ports**

**Core Services**:
| Service | Port | Status | Docs |
|---------|------|--------|------|
| Frontend | 5173 | ✅ Working | - |
| NGINX Gateway | 80 | ✅ Ready | [Architecture](02-architecture/OVERVIEW.md) |
| Player Service | 8001 | ✅ Implemented | http://localhost:8001/docs |
| Team Service | 8002 | ✅ Implemented | http://localhost:8002/docs |
| Match Service | 8003 | ✅ Implemented | http://localhost:8003/docs |
| Statistics Service | 8004 | ✅ Implemented | http://localhost:8004/docs |
| ML Service | 8005 | ✅ Implemented | http://localhost:8005/docs |
| Live Ingestion | 8006 | ✅ Implemented | http://localhost:8006/docs |
| Search Service | 8007 | ✅ Implemented | http://localhost:8007/docs |
| Notification Service | 8008 | ✅ Implemented | http://localhost:8008/docs |
| **Report Service** | **8009** | **✅ NEW** | **http://localhost:8009/docs** |
| **Export Service** | **8010** | **✅ NEW** | **http://localhost:8010/docs** |
| **Video Service** | **8011** | **✅ NEW** | **http://localhost:8011/docs** |
| **Analytics Service** | **8012** | **✅ NEW** | **http://localhost:8012/docs** |
| WebSocket Server | 8080 | ✅ Implemented | http://localhost:8080/stats |

**Infrastructure**:
| Service | Port | Status |
|---------|------|--------|
| MongoDB | 27017 | ✅ Ready |
| Redis | 6379 | ✅ Ready |
| Kafka | 9092 | ✅ Ready |
| Elasticsearch | 9200 | ✅ Ready |
| TimescaleDB | 5432 | ✅ Ready |
| MinIO | 9000 | ✅ Ready |

### **Key URLs**

- **Frontend**: http://localhost:5173
- **API Gateway**: http://localhost (when running)
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Kafka UI**: http://localhost:8090

---

## 📖 **Documentation Guidelines**

### **For Contributors**

When updating documentation:

1. **Be honest** about status (don't claim "production ready" if it's not)
2. **Include dates** at the top of documents
3. **Test commands** before documenting them
4. **Keep it current** - update when things change
5. **Avoid duplication** - link to other docs instead of repeating

### **Documentation Standards**

- Use clear, concise language
- Include code examples where helpful
- Add diagrams for complex concepts
- Link between related documents
- Keep formatting consistent

---

## 🤝 **Contributing**

Found an error in the documentation? Please:

1. Check if the issue is in [Current Status](07-status/CURRENT_STATUS.md)
2. Update the relevant document
3. Submit a pull request

---

## 📞 **Getting Help**

**Quick Help**:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Restart services
docker-compose restart
```

**Still stuck?** Check:
1. [Current Status](07-status/CURRENT_STATUS.md) - Known issues
2. [Quick Start](01-getting-started/QUICK_START.md) - Setup problems
3. [Integration Guide](04-integration/FRONTEND_BACKEND_INTEGRATION.md) - Connection issues

---

**Last Updated**: 2025-10-19
**Services**: 13 microservices fully implemented
**Status**: Feature complete, ready for integration testing

<template>
  <div class="geo-dashboard">
    <div class="header">
      <h2>🌍 地缘政治模拟监控</h2>
      <div class="controls">
        <button @click="refreshData" class="btn-refresh">🔄 刷新</button>
        <select v-model="selectedSession" @change="loadSession" class="session-select">
          <option value="">选择模拟会话</option>
          <option v-for="s in sessions" :key="s.session_id" :value="s.session_id">
            {{ s.session_id }} ({{ s.status }})
          </option>
        </select>
      </div>
    </div>

    <!-- 实时状态 -->
    <div class="status-grid">
      <div class="status-card tension">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <div class="card-label">全局紧张度</div>
          <div class="card-value">{{ currentTension }}/100</div>
          <div class="tension-bar">
            <div class="tension-fill" :style="{ width: currentTension + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="status-card">
        <div class="card-icon">💥</div>
        <div class="card-content">
          <div class="card-label">战争事件</div>
          <div class="card-value">{{ warEventsCount }}</div>
        </div>
      </div>

      <div class="status-card">
        <div class="card-icon">🏛️</div>
        <div class="card-content">
          <div class="card-label">UN决议</div>
          <div class="card-value">{{ unResolutionsCount }}</div>
        </div>
      </div>

      <div class="status-card">
        <div class="card-icon">📰</div>
        <div class="card-content">
          <div class="card-label">社交媒体动作</div>
          <div class="card-value">{{ socialMediaCount }}</div>
        </div>
      </div>
    </div>

    <!-- 国家状态 -->
    <div class="section">
      <h3>🌐 各国状态</h3>
      <div class="countries-grid">
        <div v-for="(country, id) in countries" :key="id" class="country-card" :class="country.war_intensity">
          <div class="country-header">
            <span class="country-name">{{ country.name }}</span>
            <span class="war-badge" v-if="country.war_intensity !== 'none'">
              {{ country.war_intensity }}
            </span>
          </div>
          
          <div class="country-stats">
            <div class="stat">
              <span class="stat-label">国际压力</span>
              <span class="stat-value">{{ country.international_pressure || 0 }}%</span>
            </div>
            <div class="stat">
              <span class="stat-label">国内支持</span>
              <span class="stat-value">{{ ((country.public_support || 0.5) * 100).toFixed(0) }}%</span>
            </div>
            <div class="stat">
              <span class="stat-label">政府稳定</span>
              <span class="stat-value">{{ ((country.government_stability || 0.8) * 100).toFixed(0) }}%</span>
            </div>
            <div class="stat">
              <span class="stat-label">伤亡</span>
              <span class="stat-value">{{ country.casualties || 0 }}</span>
            </div>
          </div>

          <div class="faction-bar" v-if="country.factions">
            <div class="faction-row">
              <span class="faction-name">强硬派</span>
              <div class="faction-track">
                <div class="faction-fill hardliner" 
                     :style="{ width: (country.factions.hardliners?.public_support || 0.35) * 100 + '%' }"></div>
              </div>
            </div>
            <div class="faction-row">
              <span class="faction-name">温和派</span>
              <div class="faction-track">
                <div class="faction-fill moderate" 
                     :style="{ width: (country.factions.moderates?.public_support || 0.45) * 100 + '%' }"></div>
              </div>
            </div>
            <div class="faction-row">
              <span class="faction-name">商业派</span>
              <div class="faction-track">
                <div class="faction-fill business" 
                     :style="{ width: (country.factions.business?.public_support || 0.2) * 100 + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 事件时间线 -->
    <div class="section">
      <h3>📜 事件时间线</h3>
      <div class="timeline">
        <div v-for="event in timeline" :key="event.round + event.type" 
             class="timeline-item" :class="event.type">
          <div class="timeline-round">Round {{ event.round }}</div>
          <div class="timeline-content">
            <span class="event-icon">
              {{ event.type === 'diplomatic' ? '📊' : 
                 event.type === 'war' ? '💥' : '🏛️' }}
            </span>
            <span class="event-description">{{ event.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GeopoliticalDashboard',
  
  data() {
    return {
      selectedSession: '',
      sessions: [],
      currentTension: 50,
      warEventsCount: 0,
      unResolutionsCount: 0,
      socialMediaCount: 0,
      countries: {},
      timeline: []
    }
  },
  
  mounted() {
    this.loadSessions()
    this.startAutoRefresh()
  },
  
  methods: {
    async loadSessions() {
      try {
        const response = await fetch('/api/simulation/list')
        const data = await response.json()
        this.sessions = data.data || []
      } catch (e) {
        console.error('Failed to load sessions', e)
      }
    },
    
    async loadSession() {
      if (!this.selectedSession) return
      
      try {
        // 加载geopolitical数据
        const geoRes = await fetch(`/api/geopolitical/${this.selectedSession}/summary`)
        if (geoRes.ok) {
          const geoData = await geoRes.json()
          this.applyGeoData(geoData)
        }
        
        // 加载timeline
        const timelineRes = await fetch(`/api/geopolitical/${this.selectedSession}/timeline`)
        if (timelineRes.ok) {
          this.timeline = await timelineRes.json()
        }
      } catch (e) {
        console.error('Failed to load session data', e)
      }
    },
    
    applyGeoData(data) {
      this.currentTension = data.global_tension || 50
      this.warEventsCount = data.war_events_count || 0
      this.unResolutionsCount = data.un_resolutions_count || 0
      
      if (data.countries) {
        this.countries = data.countries
      }
    },
    
    async refreshData() {
      if (this.selectedSession) {
        await this.loadSession()
      }
    },
    
    startAutoRefresh() {
      this.refreshInterval = setInterval(() => {
        if (this.selectedSession) {
          this.refreshData()
        }
      }, 5000)
    }
  },
  
  beforeDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  }
}
</script>

<style scoped>
.geo-dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.controls {
  display: flex;
  gap: 10px;
}

.btn-refresh {
  padding: 8px 16px;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.session-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 200px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 30px;
}

.status-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.status-card.tension {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.card-icon {
  font-size: 32px;
}

.card-label {
  font-size: 12px;
  opacity: 0.8;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
}

.tension-bar {
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,0.3);
  border-radius: 3px;
  margin-top: 8px;
}

.tension-fill {
  height: 100%;
  background: white;
  border-radius: 3px;
  transition: width 0.3s;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section h3 {
  margin-top: 0;
  margin-bottom: 16px;
}

.countries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.country-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s;
}

.country-card.war-none {
  border-left: 4px solid #4caf50;
}

.country-card.war-skirmish {
  border-left: 4px solid #ff9800;
}

.country-card.war-local_war,
.country-card.war-full_scale {
  border-left: 4px solid #f44336;
  background: #fff5f5;
}

.country-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.country-name {
  font-weight: bold;
  font-size: 16px;
}

.war-badge {
  background: #f44336;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-transform: uppercase;
}

.country-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 11px;
  color: #666;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
}

.faction-bar {
  border-top: 1px solid #eee;
  padding-top: 12px;
}

.faction-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.faction-name {
  width: 50px;
  font-size: 12px;
  color: #666;
}

.faction-track {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
}

.faction-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.faction-fill.hardliner {
  background: #e53935;
}

.faction-fill.moderate {
  background: #43a047;
}

.faction-fill.business {
  background: #1e88e5;
}

.timeline {
  max-height: 400px;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.timeline-item:last-child {
  border-bottom: none;
}

.timeline-round {
  width: 60px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.timeline-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-icon {
  font-size: 18px;
}

.event-description {
  font-size: 14px;
}

.timeline-item.diplomatic .event-icon { color: #4a90d9; }
.timeline-item.war .event-icon { color: #f44336; }
.timeline-item.un .event-icon { color: #764ba2; }
</style>
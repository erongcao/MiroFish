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
        <div class="card-icon">🤝</div>
        <div class="card-content">
          <div class="card-label">活跃同盟</div>
          <div class="card-value">{{ activeAlliancesCount }}</div>
        </div>
      </div>

      <div class="status-card">
        <div class="card-icon">⚠️</div>
        <div class="card-content">
          <div class="card-label">制裁事件</div>
          <div class="card-value">{{ activeSanctionsCount }}</div>
        </div>
      </div>

      <div class="status-card">
        <div class="card-icon">☢️</div>
        <div class="card-content">
          <div class="card-label">核大国</div>
          <div class="card-value">{{ nuclearPowersCount }}</div>
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

    <!-- 外交状态概览 -->
    <div class="section" v-if="diplomacySummary">
      <h3>🌐 外交状态概览</h3>
      <div class="diplomacy-grid">
        <!-- 同盟 -->
        <div class="diplomacy-card" v-if="diplomacySummary.alliances">
          <h4>🤝 同盟</h4>
          <div class="diplomacy-list">
            <div v-for="alliance in diplomacySummary.alliances.alliances" :key="alliance.alliance_id" 
                 class="alliance-item">
              <span class="alliance-name">{{ alliance.name }}</span>
              <span class="alliance-type">{{ alliance.type }}</span>
              <span class="alliance-members">{{ alliance.members.length }}国</span>
              <div class="cohesion-bar">
                <div class="cohesion-fill" :style="{ width: (alliance.cohesion * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 制裁 -->
        <div class="diplomacy-card" v-if="diplomacySummary.sanctions">
          <h4>⚠️ 制裁</h4>
          <div class="diplomacy-list">
            <div v-for="sanction in activeSanctions" :key="sanction.sanction_id" 
                 class="sanction-item">
              <span class="sanction-target">{{ sanction.target }}</span>
              <span class="sanction-imposers">被 {{ sanction.imposers.length }} 国制裁</span>
              <span class="sanction-severity" :class="sanction.severity">{{ sanction.severity }}</span>
              <span class="sanction-impact">影响: {{ (sanction.economic_impact * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <!-- 调解 -->
        <div class="diplomacy-card" v-if="diplomacySummary.mediation">
          <h4>🕊️ 调解</h4>
          <div class="mediation-stats">
            <div class="stat-row">
              <span>总尝试: {{ diplomacySummary.mediation.total_attempts }}</span>
              <span>成功率: {{ (diplomacySummary.mediation.success_rate * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <!-- 核威慑 -->
        <div class="diplomacy-card" v-if="nuclearStandoffs.length > 0">
          <h4>☢️ 核威慑对峙</h4>
          <div class="nuclear-list">
            <div v-for="(standoff, index) in nuclearStandoffs" :key="index" 
                 class="standoff-item">
              <span>{{ standoff.a }} ↔ {{ standoff.b }}</span>
              <span class="mad-prob">MAD: {{ (standoff.mad_probability * 100).toFixed(0) }}%</span>
              <span class="stability" :class="{ stable: standoff.stable }">
                {{ standoff.stable ? '稳定' : '不稳定' }}
              </span>
            </div>
          </div>
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
            <div class="country-badges">
              <span class="war-badge" v-if="country.war_intensity !== 'none'">
                {{ country.war_intensity }}
              </span>
              <span class="nuclear-badge" v-if="country.nuclear">☢️</span>
              <span class="sanction-badge" v-if="country.under_sanction">⚠️</span>
            </div>
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
              <span class="stat-label">政治资本</span>
              <span class="stat-value">{{ ((country.political_capital || 0.5) * 100).toFixed(0) }}%</span>
            </div>
            <div class="stat">
              <span class="stat-label">资源</span>
              <span class="stat-value">{{ (country.resources || 100).toFixed(0) }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">战争疲劳</span>
              <span class="stat-value">{{ ((country.war_exhaustion || 0) * 100).toFixed(0) }}%</span>
            </div>
          </div>

          <!-- 外交关系 -->
          <div class="relations-bar" v-if="country.relations">
            <div v-for="(rel, otherId) in country.relations" :key="otherId" class="relation-row">
              <span class="relation-name">{{ otherId }}</span>
              <div class="relation-track">
                <div class="relation-fill" :class="rel.state"
                     :style="{ width: ((rel.trust + 1) / 2 * 100) + '%' }"></div>
              </div>
              <span class="relation-state">{{ rel.state }}</span>
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
                 event.type === 'war' ? '💥' : 
                 event.type === 'alliance' ? '🤝' :
                 event.type === 'sanction' ? '⚠️' :
                 event.type === 'mediation' ? '🕊️' :
                 event.type === 'nuclear' ? '☢️' : '🏛️' }}
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
      activeAlliancesCount: 0,
      activeSanctionsCount: 0,
      nuclearPowersCount: 0,
      socialMediaCount: 0,
      countries: {},
      timeline: [],
      diplomacySummary: null,
      activeSanctions: [],
      nuclearStandoffs: []
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
        
        // 加载外交摘要
        const dipRes = await fetch(`/api/diplomacy/${this.selectedSession}/summary`)
        if (dipRes.ok) {
          this.diplomacySummary = await dipRes.json()
          this.processDiplomacyData()
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
      this.socialMediaCount = data.social_media_count || 0
      
      if (data.countries) {
        this.countries = data.countries
      }
    },
    
    processDiplomacyData() {
      if (!this.diplomacySummary) return
      
      // 同盟数量
      this.activeAlliancesCount = this.diplomacySummary.alliances?.active || 0
      
      // 制裁数量
      this.activeSanctionsCount = this.diplomacySummary.sanctions?.active || 0
      
      // 核大国数量
      this.nuclearPowersCount = this.diplomacySummary.nuclear_powers || 0
      
      // 活跃制裁列表
      this.activeSanctions = this.diplomacySummary.sanctions?.active_sanctions || []
      
      // 核对峙
      this.nuclearStandoffs = this.diplomacySummary.nuclear_standoffs || []
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
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

/* 外交状态概览 */
.diplomacy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.diplomacy-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
}

.diplomacy-card h4 {
  margin-top: 0;
  margin-bottom: 12px;
}

.diplomacy-list {
  max-height: 200px;
  overflow-y: auto;
}

.alliance-item, .sanction-item, .standoff-item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
  align-items: center;
}

.alliance-name {
  font-weight: 500;
}

.alliance-type {
  font-size: 12px;
  color: #666;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
}

.cohesion-bar {
  width: 60px;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
}

.cohesion-fill {
  height: 100%;
  background: #43a047;
  border-radius: 3px;
}

.sanction-severity {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}

.sanction-severity.LIGHT { background: #fff3e0; color: #e65100; }
.sanction-severity.MODERATE { background: #ffebee; color: #c62828; }
.sanction-severity.SEVERE { background: #fce4ec; color: #880e4f; }
.sanction-severity.TOTAL { background: #f3e5f5; color: #4a148c; }

.mad-prob {
  font-size: 12px;
  color: #c62828;
}

.stability {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
}

.stability.stable {
  background: #e8f5e9;
  color: #2e7d32;
}

.stability:not(.stable) {
  background: #ffebee;
  color: #c62828;
}

/* 国家卡片 */
.countries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
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

.country-badges {
  display: flex;
  gap: 4px;
}

.war-badge {
  background: #f44336;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-transform: uppercase;
}

.nuclear-badge {
  font-size: 14px;
}

.sanction-badge {
  font-size: 14px;
}

.country-stats {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
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

/* 关系条 */
.relations-bar {
  border-top: 1px solid #eee;
  padding-top: 12px;
  margin-bottom: 12px;
}

.relation-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.relation-name {
  width: 50px;
  font-size: 12px;
}

.relation-track {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
}

.relation-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.relation-fill.neutral { background: #9e9e9e; }
.relation-fill.friendly { background: #43a047; }
.relation-fill.allied { background: #1e88e5; }
.relation-fill.hostile { background: #fb8c00; }
.relation-fill.at_war { background: #e53935; }

.relation-state {
  font-size: 11px;
  color: #666;
  width: 50px;
}

/* 派系 */
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

/* 时间线 */
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
.timeline-item.alliance .event-icon { color: #43a047; }
.timeline-item.sanction .event-icon { color: #fb8c00; }
.timeline-item.mediation .event-icon { color: #8e24aa; }
.timeline-item.nuclear .event-icon { color: #e53935; }
.timeline-item.un .event-icon { color: #764ba2; }
</style>
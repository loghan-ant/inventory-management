<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.subtitle') }}</p>
    </div>

    <!-- Budget Control Card -->
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
      </div>
      <div class="budget-control">
        <input
          type="range"
          min="0"
          max="50000"
          step="500"
          v-model.number="budget"
          @input="onBudgetChange"
          class="budget-slider"
        />
        <span class="budget-value">{{ formatCurrency(budget) }}</span>
      </div>
    </div>

    <!-- Summary Row -->
    <div class="stats-grid summary-grid" v-if="recommendations">
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.budget') }}</div>
        <div class="stat-value summary-value">{{ formatCurrency(recommendations.budget) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.totalCost') }}</div>
        <div class="stat-value summary-value">{{ formatCurrency(recommendations.total_cost) }}</div>
      </div>
      <div class="stat-card" :class="{ success: recommendations.remaining_budget >= 0, danger: recommendations.remaining_budget < 0 }">
        <div class="stat-label">{{ t('restocking.remaining') }}</div>
        <div class="stat-value summary-value">{{ formatCurrency(recommendations.remaining_budget) }}</div>
      </div>
    </div>

    <!-- Recommendations Card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="!recommendations || recommendations.items.length === 0" class="no-items">
        {{ t('restocking.noItems') }}
      </div>
      <div v-else>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.gap') }}</th>
                <th>{{ t('restocking.table.qty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations.items"
                :key="item.item_sku"
                :class="{ excluded: !item.included }"
              >
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.demand_gap }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td><strong>{{ formatCurrency(item.line_cost) }}</strong></td>
                <td>{{ item.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="excluded-hint">{{ t('restocking.excludedHint') }}</p>
      </div>
    </div>

    <!-- Place Order Actions -->
    <div class="order-actions" v-if="recommendations && recommendations.items.length > 0">
      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      <div v-if="submitError" class="error submit-error">{{ submitError }}</div>
      <button
        class="btn-primary"
        :disabled="includedItems.length === 0 || submitting"
        @click="placeOrder"
      >
        {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    const budget = ref(10000)
    const loading = ref(false)
    const error = ref(null)
    const recommendations = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)

    let debounceTimer = null

    const includedItems = computed(() => {
      if (!recommendations.value) return []
      return recommendations.value.items.filter(i => i.included)
    })

    const formatCurrency = (value) => {
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        recommendations.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const onBudgetChange = () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 250)
    }

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      successMessage.value = null
      try {
        const payload = {
          budget: budget.value,
          items: includedItems.value.map(i => ({
            item_sku: i.item_sku,
            item_name: i.item_name,
            category: i.category,
            quantity: i.recommended_quantity,
            unit_cost: i.unit_cost,
            line_cost: i.line_cost
          }))
        }
        const result = await api.submitRestockOrder(payload)
        successMessage.value = t('restocking.orderPlaced', { n: result.order_number })
        setTimeout(() => { successMessage.value = null }, 5000)
        await loadRecommendations()
      } catch (err) {
        submitError.value = 'Failed to submit order: ' + err.message
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      budget,
      loading,
      error,
      recommendations,
      submitting,
      submitError,
      successMessage,
      includedItems,
      formatCurrency,
      onBudgetChange,
      placeOrder
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin-bottom: 0.25rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-control {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.5rem 0;
}

.budget-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 130px;
  text-align: right;
  letter-spacing: -0.025em;
}

.summary-grid {
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 1.25rem;
}

.summary-value {
  font-size: 1.5rem;
}

.excluded {
  opacity: 0.45;
}

.excluded td {
  color: #94a3b8;
}

.excluded strong {
  color: #94a3b8;
}

.excluded-hint {
  font-size: 0.8rem;
  color: #94a3b8;
  margin-top: 0.75rem;
  padding: 0 0.75rem 0.5rem;
}

.no-items {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.25rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.success-message {
  padding: 0.625rem 1rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid #6ee7b7;
}

.submit-error {
  padding: 0.5rem 1rem;
  margin: 0;
  border-radius: 8px;
  font-size: 0.875rem;
}

.loading {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.error {
  padding: 2rem;
  text-align: center;
  color: #ef4444;
}
</style>

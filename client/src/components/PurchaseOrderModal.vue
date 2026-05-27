<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="emit('close')">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}
            </h3>
            <button class="close-button" @click="emit('close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item context -->
            <div class="context-section">
              <div class="context-grid">
                <div class="context-item">
                  <div class="context-label">Item</div>
                  <div class="context-value">{{ backlogItem.item_name }}</div>
                </div>
                <div class="context-item">
                  <div class="context-label">SKU</div>
                  <div class="context-value mono">{{ backlogItem.item_sku }}</div>
                </div>
                <div class="context-item">
                  <div class="context-label">Order ID</div>
                  <div class="context-value mono">{{ backlogItem.order_id }}</div>
                </div>
                <div class="context-item">
                  <div class="context-label">Shortage</div>
                  <div class="context-value shortage">{{ shortage }} units</div>
                </div>
              </div>
            </div>

            <!-- Create mode: form -->
            <div v-if="mode === 'create'" class="form-section">
              <div v-if="submitError" class="inline-error">{{ submitError }}</div>

              <div class="form-grid">
                <div class="form-group full-width">
                  <label for="po-supplier">Supplier Name <span class="required">*</span></label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier_name"
                    type="text"
                    class="form-input"
                    placeholder="Enter supplier name"
                  />
                </div>

                <div class="form-group">
                  <label for="po-quantity">Quantity <span class="required">*</span></label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    class="form-input"
                    min="1"
                    placeholder="0"
                  />
                </div>

                <div class="form-group">
                  <label for="po-unit-cost">Unit Cost (USD) <span class="required">*</span></label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    class="form-input"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                  />
                </div>

                <div class="form-group full-width">
                  <label for="po-delivery-date">Expected Delivery Date <span class="required">*</span></label>
                  <input
                    id="po-delivery-date"
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="form-input"
                  />
                </div>

                <div class="form-group full-width">
                  <label for="po-notes">Notes</label>
                  <textarea
                    id="po-notes"
                    v-model="form.notes"
                    class="form-textarea"
                    rows="3"
                    placeholder="Optional notes for this purchase order"
                  ></textarea>
                </div>
              </div>

              <!-- Cost preview -->
              <div v-if="form.quantity && form.unit_cost" class="cost-preview">
                <span class="cost-label">Estimated Total</span>
                <span class="cost-value">{{ formatCost(form.quantity * form.unit_cost) }}</span>
              </div>
            </div>

            <!-- View mode: PO details -->
            <div v-else class="view-section">
              <div v-if="poLoading" class="state-message">Loading purchase order...</div>
              <div v-else-if="poError" class="state-message error-message">{{ poError }}</div>
              <div v-else-if="purchaseOrder" class="po-details">
                <div class="detail-grid">
                  <div class="detail-item">
                    <div class="detail-label">Supplier</div>
                    <div class="detail-value">{{ purchaseOrder.supplier_name }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">
                      <span class="status-badge" :class="purchaseOrder.status">{{ purchaseOrder.status }}</span>
                    </div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">Quantity</div>
                    <div class="detail-value">{{ purchaseOrder.quantity }} units</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">Unit Cost</div>
                    <div class="detail-value">{{ formatCost(purchaseOrder.unit_cost) }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">Total Cost</div>
                    <div class="detail-value total-cost">{{ formatCost(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">Expected Delivery</div>
                    <div class="detail-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                  </div>
                  <div class="detail-item">
                    <div class="detail-label">Created</div>
                    <div class="detail-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                  </div>
                  <div v-if="purchaseOrder.notes" class="detail-item full-width">
                    <div class="detail-label">Notes</div>
                    <div class="detail-value notes-value">{{ purchaseOrder.notes }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="emit('close')">
              {{ mode === 'create' ? 'Cancel' : 'Close' }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="!isFormValid || submitting"
              @click="handleSubmit"
            >
              {{ submitting ? 'Submitting...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create',
    validator: (val) => ['create', 'view'].includes(val)
  }
})

const emit = defineEmits(['close', 'po-created'])

// Form state (create mode)
const form = ref({
  supplier_name: '',
  quantity: 0,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

// Submit state
const submitting = ref(false)
const submitError = ref(null)

// View mode state
const purchaseOrder = ref(null)
const poLoading = ref(false)
const poError = ref(null)

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const isFormValid = computed(() => {
  return (
    form.value.supplier_name.trim() !== '' &&
    form.value.quantity > 0 &&
    form.value.unit_cost > 0 &&
    form.value.expected_delivery_date !== ''
  )
})

const resetForm = () => {
  form.value = {
    supplier_name: '',
    quantity: shortage.value,
    unit_cost: null,
    expected_delivery_date: '',
    notes: ''
  }
  submitError.value = null
}

// When the modal opens, set up state based on mode
watch(
  () => [props.isOpen, props.mode],
  ([open, mode]) => {
    if (!open) return

    if (mode === 'create') {
      resetForm()
    } else if (mode === 'view') {
      fetchPurchaseOrder()
    }
  },
  { immediate: true }
)

const fetchPurchaseOrder = async () => {
  if (!props.backlogItem) return
  purchaseOrder.value = null
  poError.value = null
  poLoading.value = true
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    if (err.response && err.response.status === 404) {
      poError.value = 'No purchase order found for this backlog item.'
    } else {
      poError.value = 'Failed to load purchase order details.'
    }
  } finally {
    poLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value || submitting.value) return
  submitting.value = true
  submitError.value = null
  try {
    const payload = {
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name.trim(),
      quantity: form.value.quantity,
      unit_cost: form.value.unit_cost,
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes.trim()
    }
    const createdPO = await api.createPurchaseOrder(payload)
    emit('po-created', createdPO)
    emit('close')
  } catch (err) {
    submitError.value = err.response?.data?.detail || 'Failed to create purchase order. Please try again.'
  } finally {
    submitting.value = false
  }
}

const formatCost = (value) => {
  if (value == null || isNaN(value)) return '-'
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  // Date-only strings (YYYY-MM-DD) parse as UTC midnight, causing toLocaleDateString
  // to show the previous day in timezones behind UTC. Append T00:00:00 (no timezone
  // suffix) so the value is treated as local midnight instead.
  const normalized = /^\d{4}-\d{2}-\d{2}$/.test(dateString)
    ? `${dateString}T00:00:00`
    : dateString
  const date = new Date(normalized)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Backlog context section */
.context-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.context-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.context-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.context-value {
  font-size: 0.938rem;
  font-weight: 500;
  color: #0f172a;
}

.context-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
  font-size: 0.875rem;
}

.context-value.shortage {
  color: #dc2626;
  font-weight: 700;
}

/* Create mode form */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.inline-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  color: #dc2626;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.required {
  color: #ef4444;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease;
  background: white;
  resize: vertical;
  min-height: 80px;
}

.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.cost-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.cost-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e40af;
}

.cost-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1e40af;
}

/* View mode PO details */
.view-section {
  min-height: 80px;
}

.state-message {
  font-size: 0.938rem;
  color: #64748b;
  text-align: center;
  padding: 2rem 0;
}

.error-message {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 1rem;
  text-align: left;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.detail-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.detail-value.total-cost {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.detail-value.notes-value {
  font-weight: 400;
  color: #475569;
  line-height: 1.5;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge.pending,
.status-badge.submitted {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.approved,
.status-badge.fulfilled {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.cancelled,
.status-badge.rejected {
  background: #fecaca;
  color: #991b1b;
}

.status-badge.in_transit,
.status-badge.in-transit {
  background: #dbeafe;
  color: #1e40af;
}

/* Footer */
.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #3b82f6;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>

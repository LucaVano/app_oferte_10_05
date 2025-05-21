/**
 * Accessory Manager - Handles adding and removing accessories for single products
 */

// Initialize the accessory management functionality for a specific tab
function setupAccessoryManagement(tabIndex) {
    const addBtn = document.querySelector(`.add-accessory-btn[data-tab-index="${tabIndex}"]`);
    
    if (!addBtn) return;
    
    // Load existing accessories from hidden input
    loadAccessories(tabIndex);
    
    // Add click event for the add button
    addBtn.addEventListener('click', function() {
        addAccessory(tabIndex);
    });
    
    // Add event listeners to remove buttons
    setupRemoveButtons(tabIndex);
    
    // Add event listener to the form for submission
    const form = document.querySelector(`#accessories_data_${tabIndex}`).closest('form');
    if (form) {
        form.addEventListener('submit', function() {
            // Ensure accessories are properly saved before form submission
            validateAccessoriesData(tabIndex);
        });
    }
}

// Load existing accessories from the hidden input
function loadAccessories(tabIndex) {
    const dataInput = document.getElementById(`accessories_data_${tabIndex}`);
    if (!dataInput) return;
    
    try {
        const accessories = JSON.parse(dataInput.value);
        // If we have accessories already loaded, we don't need to do anything
        if (document.querySelectorAll(`#accessories_table_${tabIndex} tbody tr`).length > 0) {
            return;
        }
        
        // Otherwise, populate the table
        const tableBody = document.querySelector(`#accessories_table_${tabIndex} tbody`);
        tableBody.innerHTML = '';
        
        accessories.forEach(accessory => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${accessory.name}</td>
                <td>${accessory.code}</td>
                <td>${accessory.price}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-accessory-btn">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // Setup remove buttons
        setupRemoveButtons(tabIndex);
        
        // Log the loaded accessories for debugging
        console.log(`Loaded ${accessories.length} accessories for tab ${tabIndex}:`, accessories);
        
    } catch (error) {
        console.error("Error loading accessories:", error);
        // Reset to empty array in case of parsing error
        dataInput.value = '[]';
    }
}

// Add a new accessory
function addAccessory(tabIndex) {
    const nameInput = document.getElementById(`accessory_name_${tabIndex}`);
    const codeInput = document.getElementById(`accessory_code_${tabIndex}`);
    const priceInput = document.getElementById(`accessory_price_${tabIndex}`);
    const tableBody = document.querySelector(`#accessories_table_${tabIndex} tbody`);
    const dataInput = document.getElementById(`accessories_data_${tabIndex}`);
    
    // Validate inputs
    if (!nameInput.value.trim()) {
        alert('Il nome dell\'accessorio è obbligatorio');
        return;
    }
    
    // Get existing accessories
    let accessories = [];
    try {
        accessories = JSON.parse(dataInput.value);
        if (!Array.isArray(accessories)) {
            console.warn('Accessories data is not an array, resetting to empty array');
            accessories = [];
        }
    } catch (error) {
        console.warn('Error parsing accessories data, resetting to empty array', error);
        accessories = [];
    }
    
    // Create new accessory object
    const newAccessory = {
        name: nameInput.value.trim(),
        code: codeInput.value.trim(),
        price: priceInput.value ? parseFloat(priceInput.value).toFixed(2) : "0.00"
    };
    
    // Add to accessories array
    accessories.push(newAccessory);
    
    // Update hidden input with stringified data
    dataInput.value = JSON.stringify(accessories);
    
    // Add row to table
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${newAccessory.name}</td>
        <td>${newAccessory.code}</td>
        <td>${newAccessory.price}</td>
        <td>
            <button type="button" class="btn btn-sm btn-outline-danger remove-accessory-btn">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tableBody.appendChild(row);
    
    // Clear form inputs
    nameInput.value = '';
    codeInput.value = '';
    priceInput.value = '';
    
    // Setup remove button for new row
    row.querySelector('.remove-accessory-btn').addEventListener('click', function() {
        removeAccessory(tabIndex, row);
    });
    
    // Log for debugging
    console.log(`Added accessory to tab ${tabIndex}. Current accessories:`, accessories);
    console.log(`Hidden input value:`, dataInput.value);
}

// Remove an accessory
function removeAccessory(tabIndex, row) {
    const dataInput = document.getElementById(`accessories_data_${tabIndex}`);
    const tableBody = document.querySelector(`#accessories_table_${tabIndex} tbody`);
    
    // Get row index
    const rowIndex = Array.from(tableBody.children).indexOf(row);
    
    // Get existing accessories
    let accessories = [];
    try {
        accessories = JSON.parse(dataInput.value);
        if (!Array.isArray(accessories)) {
            console.warn('Accessories data is not an array, resetting to empty array');
            accessories = [];
        }
    } catch (error) {
        console.warn('Error parsing accessories data, resetting to empty array', error);
        accessories = [];
    }
    
    // Remove the accessory
    if (rowIndex >= 0 && rowIndex < accessories.length) {
        accessories.splice(rowIndex, 1);
    }
    
    // Update hidden input
    dataInput.value = JSON.stringify(accessories);
    
    // Remove row from table
    row.remove();
    
    // Log for debugging
    console.log(`Removed accessory from tab ${tabIndex}. Current accessories:`, accessories);
}

// Setup remove buttons for all accessories
function setupRemoveButtons(tabIndex) {
    const table = document.getElementById(`accessories_table_${tabIndex}`);
    if (!table) return;
    
    const removeButtons = table.querySelectorAll('.remove-accessory-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const row = button.closest('tr');
            removeAccessory(tabIndex, row);
        });
    });
}

// Validate accessories data before form submission
function validateAccessoriesData(tabIndex) {
    const dataInput = document.getElementById(`accessories_data_${tabIndex}`);
    if (!dataInput) return;
    
    try {
        // Make sure the data is valid JSON
        const accessories = JSON.parse(dataInput.value);
        
        // Ensure it's an array
        if (!Array.isArray(accessories)) {
            console.warn('Accessories data is not an array, resetting to empty array');
            dataInput.value = '[]';
        }
        
        // Check if the array matches the table rows
        const tableRows = document.querySelectorAll(`#accessories_table_${tabIndex} tbody tr`).length;
        if (accessories.length !== tableRows) {
            console.warn(`Mismatch between accessories array (${accessories.length}) and table rows (${tableRows})`);
        }
        
        // Log for verification
        console.log(`Accessory data validated for tab ${tabIndex}. Found ${accessories.length} accessories.`);
    } catch (error) {
        console.error("Error validating accessories data:", error);
        // Reset to empty array in case of parsing error
        dataInput.value = '[]';
    }
}

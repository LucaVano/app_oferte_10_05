/**
 * Script principale per l'applicazione Generatore Offerte
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inizializza i tooltip Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Chiudi automaticamente gli alert dopo 5 secondi
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var alertInstance = new bootstrap.Alert(alert);
            alertInstance.close();
        });
    }, 5000);

    // Formatta i campi numerici con separatore delle migliaia
    document.querySelectorAll('input[type="number"]').forEach(function(input) {
        input.addEventListener('change', function() {
            var value = parseFloat(this.value);
            if (!isNaN(value)) {
                if (this.step === '0.01' || this.step === 'any') {
                    // Formatta con 2 decimali per i campi monetari
                    this.value = value.toFixed(2);
                } else {
                    // Arrotonda all'intero per gli altri campi
                    this.value = Math.round(value);
                }
            }
        });
    });

    // Gestione dinamica del form per la creazione/modifica dell'offerta
    const offerForm = document.getElementById('offerForm');
    if (offerForm) {
        // Controlla se i campi obbligatori sono compilati prima di inviare il form
        offerForm.addEventListener('submit', function(event) {
            var requiredFields = offerForm.querySelectorAll('[required]');
            var valid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    valid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!valid) {
                event.preventDefault();
                alert('Compila tutti i campi obbligatori prima di continuare.');
                // Scorri fino al primo campo non valido
                var firstInvalid = offerForm.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
        });
        
        // Rimuovi la classe is-invalid quando l'utente modifica il campo
        offerForm.querySelectorAll('.form-control').forEach(function(input) {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
            });
        });
    }

    // Gestione della data corrente per i nuovi form
    const dateInput = document.getElementById('date');
    if (dateInput && !dateInput.value) {
        const today = new Date();
        const year = today.getFullYear();
        let month = today.getMonth() + 1;
        let day = today.getDate();
        
        // Aggiungi zero iniziale se necessario
        month = month < 10 ? '0' + month : month;
        day = day < 10 ? '0' + day : day;
        
        dateInput.value = `${year}-${month}-${day}`;
    }

    // Gestione del campo numero offerta
    const offerNumberInput = document.getElementById('offer_number');
    const updateCounterCheckbox = document.getElementById('update_counter');
    
    if (offerNumberInput && updateCounterCheckbox) {
        // Se l'utente modifica manualmente il numero, attiva il checkbox
        offerNumberInput.addEventListener('input', function() {
            if (this.value.trim() !== '' && this.defaultValue !== this.value) {
                updateCounterCheckbox.checked = true;
            }
        });
    }

    // Aggiorna i totali nella visualizzazione dell'offerta
    function updateTotals() {
        let grandTotal = 0;
        
        // Calcola il totale dei prodotti singoli
        document.querySelectorAll('.alert-info h3[data-price]').forEach(priceElement => {
            const price = parseFloat(priceElement.getAttribute('data-price')) || 0;
            grandTotal += price;
            priceElement.textContent = formatPrice(price) + ' €';
        });
        
        // Calcola il totale dei prodotti multipli e aggiorna i conteggi
        document.querySelectorAll('#multi-product-total').forEach(totalElement => {
            const total = parseFloat(totalElement.getAttribute('data-total')) || 0;
            grandTotal += total;
            totalElement.textContent = formatPrice(total) + ' €';
        });
        
        // Aggiorna il prezzo totale
        const totalPriceElement = document.getElementById('totalPrice');
        if (totalPriceElement) {
            // Arrotonda alla decina più vicina
            const roundedTotal = Math.round(grandTotal / 10) * 10;
            totalPriceElement.textContent = '€ ' + formatPrice(roundedTotal);
        }
    }
    
    // Chiama updateTotals solo se ci sono elementi price/quantity nella pagina
    if (document.querySelector('.product-price')) {
        updateTotals();
    }

    // Inizializza i contatori di caratteri
    initCharacterCounters();

    // Inizializza l'auto-espansione dei textarea
    initAutoExpandTextareas();

    // Gestione dei textarea per prodotti multipli
    handleMultiProductTextarea();
    
    // Imposta il calcolo dello sconto in tempo reale
    setupDiscountCalculation();
});

/**
 * Funzioni globali per il conteggio caratteri
 */

// Funzione generica per contare caratteri in un elemento textarea o input
function countCharacters(element, counter, maxLength) {
    if (!element || !counter) return;
    
    const currentLength = element.value.length;
    const counterElement = typeof counter === 'string' ? document.getElementById(counter) : counter;
    
    if (counterElement) {
        const spanElement = counterElement.querySelector('span') || counterElement;
        spanElement.textContent = currentLength;
        
        // Cambia colore se si avvicina al limite
        if (currentLength >= maxLength * 0.9) {
            counterElement.classList.add('text-danger');
            counterElement.classList.remove('text-muted');
        } else {
            counterElement.classList.add('text-muted');
            counterElement.classList.remove('text-danger');
        }
    }
}

// Funzione per inizializzare tutti i contatori nella pagina
function initCharacterCounters() {
    // Inizializza per tutti i textarea con attributo maxlength
    document.querySelectorAll('textarea[maxlength]').forEach(function(textarea) {
        const maxLength = parseInt(textarea.getAttribute('maxlength'), 10);
        const counterId = 'counter_' + textarea.id;
        
        // Crea un contatore se non esiste già
        let counter = document.getElementById(counterId);
        if (!counter) {
            counter = document.createElement('small');
            counter.id = counterId;
            counter.className = 'form-text text-muted char-counter';
            counter.style.cssText = 'display: block; text-align: right; position: absolute; bottom: 0; right: 10px;';
            counter.innerHTML = `<span>0</span>/${maxLength} caratteri`;
            
            // Inserisci il contatore accanto al textarea
            const parent = textarea.parentElement;
            if (parent) {
                if (!parent.style.position || parent.style.position === 'static') {
                    parent.style.position = 'relative';
                }
                parent.appendChild(counter);
            }
        }
        
        // Aggiorna il contatore inizialmente
        countCharacters(textarea, counter, maxLength);
        
        // Aggiungi event listener
        textarea.addEventListener('input', function() {
            countCharacters(this, counter, maxLength);
        });
    });
    
    // Inizializza per tutti gli input di testo con attributo maxlength
    document.querySelectorAll('input[type="text"][maxlength]').forEach(function(input) {
        const maxLength = parseInt(input.getAttribute('maxlength'), 10);
        const counterId = 'counter_' + input.id;
        
        // Crea un contatore se non esiste già e se l'input è abbastanza importante (descrizioni)
        if (input.name && (input.name.includes('description') || input.name.includes('descrizione'))) {
            let counter = document.getElementById(counterId);
            if (!counter) {
                counter = document.createElement('small');
                counter.id = counterId;
                counter.className = 'form-text text-muted char-counter';
                counter.style.cssText = 'display: block; text-align: right; font-size: 0.75rem;';
                counter.innerHTML = `<span>0</span>/${maxLength} caratteri`;
                
                // Inserisci il contatore dopo l'input
                input.insertAdjacentElement('afterend', counter);
            }
            
            // Aggiorna il contatore inizialmente
            countCharacters(input, counter, maxLength);
            
            // Aggiungi event listener
            input.addEventListener('input', function() {
                countCharacters(this, counter, maxLength);
            });
        }
    });
}

// Funzione per aggiornare il contatore di caratteri
function updateCharCount(textareaId, counterId) {
    const textarea = document.getElementById(textareaId);
    const counter = document.getElementById(counterId);
    
    if (textarea && counter) {
        const currentLength = textarea.value.length;
        counter.querySelector('span').textContent = currentLength;
    }
}

// Funzione per aggiornare il contatore di caratteri per i prodotti multipli
function updateMultiProdCharCount(input) {
    const counter = input.nextElementSibling.querySelector('span');
    const currentLength = input.value.length;
    counter.textContent = currentLength;
}

// Funzione per aggiornare il contatore di caratteri (usata direttamente dagli elementi HTML)
function updateCharCount(textareaId, counterId, maxLength) {
    const textarea = document.getElementById(textareaId);
    const counter = document.getElementById(counterId);
    
    if (textarea && counter) {
        const currentLength = textarea.value.length;
        counter.querySelector('span').textContent = currentLength;
        
        // Cambia colore se si avvicina al limite
        if (currentLength >= maxLength * 0.9) {
            counter.classList.add('text-danger');
            counter.classList.remove('text-muted');
        } else {
            counter.classList.add('text-muted');
            counter.classList.remove('text-danger');
        }
    }
}

// Funzione per aggiornare il contatore di caratteri per i prodotti multipli
function updateMultiProdCharCount(input, maxLength) {
    const counter = input.nextElementSibling.querySelector('span');
    const currentLength = input.value.length;
    
    counter.textContent = currentLength;
    
    // Cambia colore se si avvicina al limite
    if (currentLength >= maxLength * 0.9) {
        counter.parentElement.classList.add('text-danger');
        counter.parentElement.classList.remove('text-muted');
    } else {
        counter.parentElement.classList.add('text-muted');
        counter.parentElement.classList.remove('text-danger');
    }
}

/**
 * Funzione per formattare i prezzi
 */
function formatPrice(value) {
    try {
        const num = parseFloat(value);
        if (isNaN(num)) return "0,00";
        
        const integerPart = Math.floor(num);
        const decimalPart = Math.round((num - integerPart) * 100);
        
        const formattedInteger = integerPart.toLocaleString('it-IT').replace(/\./g, ',').replace(/,/g, '.');
        return `${formattedInteger},${decimalPart.toString().padStart(2, '0')}`;
    } catch (error) {
        return "0,00";
    }
}

/**
 * Funzione per gestire l'auto-espansione dei textarea
 */
function initAutoExpandTextareas() {
    // Handle regular textareas
    document.querySelectorAll('textarea.auto-expand').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Set initial height
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    });

    // Handle table textareas
    document.querySelectorAll('textarea.auto-expand-table').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = '38px';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Set initial height
        if (textarea.value) {
            textarea.style.height = '38px';
            textarea.style.height = (textarea.scrollHeight) + 'px';
        }
    });
}

/**
 * Aggiorna la gestione dei textarea per prodotti multipli
 */
function handleMultiProductTextarea() {
    document.querySelectorAll('textarea.auto-expand').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            updateMultiProdCharCount(this, parseInt(this.getAttribute('maxlength')) || 200);
        });
        
        // Set initial height
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
        updateMultiProdCharCount(textarea, parseInt(this.getAttribute('maxlength')) || 200);
    });
}

/**
 * Aggiungi la funzione al gestore delle schede
 */
function handleNewTab() {
    initAutoExpandTextareas();
}

/**
 * Funzione per calcolare e mostrare il prezzo scontato
 */
function updateDiscountedPrice(tabIndex) {
    const discountInput = document.getElementById(`discount_${tabIndex}`);
    const priceInput = document.getElementById(`unit_${tabIndex}price_`);
    const discountFlagCheckbox = document.getElementById(`discount_flag_${tabIndex}`);
    const discountedPriceElement = document.getElementById(`discounted_price_${tabIndex}`);
    
    if (discountInput && priceInput && discountedPriceElement) {
        const discount = parseFloat(discountInput.value) || 0;
        const price = parseFloat(priceInput.value) || 0;
        
        // Calcola il prezzo scontato solo se lo sconto è attivo
        if (discountFlagCheckbox && discountFlagCheckbox.checked) {
            const discountedPrice = price * (1 - discount/100);
            discountedPriceElement.textContent = formatPrice(discountedPrice) + ' €';
            discountedPriceElement.parentElement.classList.remove('text-muted');
            discountedPriceElement.parentElement.classList.add('text-success');
        } else {
            discountedPriceElement.textContent = formatPrice(price) + ' €';
            discountedPriceElement.parentElement.classList.add('text-muted');
            discountedPriceElement.parentElement.classList.remove('text-success');
        }
    }
}

// Aggiungiamo un listener per il campo prezzo unitario
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[id^="unit_"][id$="price_"]').forEach(input => {
        input.addEventListener('input', function() {
            const tabIndex = this.id.replace('unit_', '').replace('price_', '');
            updateDiscountedPrice(tabIndex);
        });
    });
});

// Modifichiamo la funzione toggleDiscount esistente
function toggleDiscount(checkbox) {
    const index = checkbox.id.replace('discount_flag_', '');
    const discountInput = document.getElementById('discount_' + index);
    
    if (discountInput) {
        discountInput.disabled = !checkbox.checked;
        console.log("Toggle sconto per indice " + index + ": " + checkbox.checked);
        updateDiscountedPrice(index);
    }
}

// Aggiungi questa nuova funzione per calcolare e mostrare il prezzo scontato in tempo reale
function setupDiscountCalculation() {
    document.querySelectorAll('.discount-checkbox').forEach(checkbox => {
        const tabIndex = checkbox.id.replace('discount_flag_', '');
        const priceInput = document.getElementById(`unit_${tabIndex}price_`);
        const quantityInput = document.getElementById(`quantity_${tabIndex}`);
        const discountInput = document.getElementById(`discount_${tabIndex}`);
        
        if (priceInput && quantityInput && discountInput) {
            // Funzione per calcolare e mostrare il prezzo scontato
            const updateDiscountedPrice = () => {
                if (checkbox.checked) {
                    const price = parseFloat(priceInput.value) || 0;
                    const quantity = parseFloat(quantityInput.value) || 1;
                    const discount = parseFloat(discountInput.value) || 0;
                    
                    const totalPrice = price * quantity;
                    const discountAmount = totalPrice * (discount / 100);
                    const discountedPrice = totalPrice - discountAmount;
                    
                    // Trova o crea l'elemento per mostrare il prezzo scontato
                    let discountedPriceElement = document.getElementById(`discounted_price_${tabIndex}`);
                    if (!discountedPriceElement) {
                        discountedPriceElement = document.createElement('p');
                        discountedPriceElement.id = `discounted_price_${tabIndex}`;
                        discountedPriceElement.className = 'text-success mt-2';
                        discountInput.parentNode.appendChild(discountedPriceElement);
                    }
                    
                    discountedPriceElement.innerHTML = `<strong>Prezzo scontato:</strong> ${formatPrice(discountedPrice)} €`;
                } else {
                    // Rimuovi l'elemento se lo sconto non è attivo
                    const discountedPriceElement = document.getElementById(`discounted_price_${tabIndex}`);
                    if (discountedPriceElement) {
                        discountedPriceElement.remove();
                    }
                }
            };
            
            // Collega gli eventi ai campi
            checkbox.addEventListener('change', updateDiscountedPrice);
            priceInput.addEventListener('input', updateDiscountedPrice);
            quantityInput.addEventListener('input', updateDiscountedPrice);
            discountInput.addEventListener('input', updateDiscountedPrice);
            
            // Esegui il calcolo iniziale
            updateDiscountedPrice();
        }
    });
}

// Aggiungiamo il calcolo dello sconto anche al caricamento iniziale della pagina
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...

    // Inizializza il calcolo dello sconto per tutti i campi esistenti
    setupDiscountCalculation();

    // Aggiungi event listener per i nuovi campi creati dinamicamente
    document.querySelectorAll('#addSingleProductBtn, #addMultiProductBtn').forEach(button => {
        button.addEventListener('click', function() {
            setTimeout(() => {
                setupDiscountCalculation(); // Reinizializza il calcolo dello sconto per i nuovi campi
            }, 100); // Ritardo per assicurarsi che i nuovi campi siano stati aggiunti al DOM
        });
    });
});
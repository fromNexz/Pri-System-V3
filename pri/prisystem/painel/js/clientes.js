document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("customers-body");
  const modal = document.getElementById("block-modal");
  const modalText = document.getElementById("block-modal-text");
  const reasonInput = document.getElementById("block-reason");
  const cancelBtn = document.getElementById("block-cancel");
  const confirmBtn = document.getElementById("block-confirm");

  let currentCustomer = null;

  function formatDate(d) {
    if (!d) return "-";
    const date = new Date(d);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleDateString("pt-BR");
  }

  function openModal(customer) {
    currentCustomer = customer;
    modalText.textContent = `${customer.name || ""} (${customer.phone})`;
    reasonInput.value = "";
    modal.classList.remove("hidden");
  }

  function closeModal() {
    currentCustomer = null;
    modal.classList.add("hidden");
  }

  cancelBtn.addEventListener("click", closeModal);

  confirmBtn.addEventListener("click", async () => {
    if (!currentCustomer) return;
    const reason = reasonInput.value.trim() || "Bloqueado via painel";

    confirmBtn.disabled = true;
    try {
      await window.blockCustomer(currentCustomer.id, reason);
      await loadCustomers(); // recarrega tabela
    } catch (err) {
      console.error(err);
      alert("Erro ao bloquear cliente.");
    } finally {
      confirmBtn.disabled = false;
      closeModal();
    }
  });

  async function loadCustomers() {
    tbody.innerHTML = "<tr><td colspan='6'>Carregando...</td></tr>";
    try {
      const customers = await window.getCustomers();
      tbody.innerHTML = "";

      if (!customers.length) {
        tbody.innerHTML = "<tr><td colspan='6'>Nenhum cliente encontrado.</td></tr>";
        return;
      }

      for (const c of customers) {
        const tr = document.createElement("tr");

        const tdName = document.createElement("td");
        tdName.textContent = c.name || "-";
        tr.appendChild(tdName);

        const tdPhone = document.createElement("td");
        tdPhone.textContent = c.phone;
        tr.appendChild(tdPhone);

        const tdCount = document.createElement("td");
        tdCount.textContent = c.total_appointments || 0;
        tr.appendChild(tdCount);

        const tdLast = document.createElement("td");
        tdLast.textContent = formatDate(c.last_appointment_date);
        tr.appendChild(tdLast);

        const tdStatus = document.createElement("td");
        const badge = document.createElement("span");
        badge.textContent = c.is_blocked ? "Bloqueado" : "Ativo";
        badge.className = c.is_blocked ? "badge badge-danger" : "badge badge-success";
        tdStatus.appendChild(badge);
        tr.appendChild(tdStatus);

        const tdActions = document.createElement("td");
        const btn = document.createElement("button");
        if (c.is_blocked) {
          btn.textContent = "Desbloquear";
          btn.className = "btn";
          btn.addEventListener("click", async () => {
            try {
              await window.unblockCustomer(c.id);
              await loadCustomers();
            } catch (err) {
              console.error(err);
              alert("Erro ao desbloquear cliente.");
            }
          });
        } else {
          btn.textContent = "Bloquear";
          btn.className = "btn btn-danger";
          btn.addEventListener("click", () => openModal(c));
        }
        tdActions.appendChild(btn);
        tr.appendChild(tdActions);

        tbody.appendChild(tr);
      }
    } catch (err) {
      console.error(err);
      tbody.innerHTML = "<tr><td colspan='6'>Erro ao carregar clientes.</td></tr>";
    }
  }

  loadCustomers();
});

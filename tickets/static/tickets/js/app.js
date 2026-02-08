/* js/app.js */

const STATUS_LIST = [
    "Aberto", "Em andamento", "Com Bloqueio", "Aguardando Validação",
    "Em migração", "Concluído", "Documentação Pendente"
];

// --- 2. FUNÇÕES DE UTILIDADE ---

function getTickets() {
    return JSON.parse(localStorage.getItem('sys_tickets')) || [];
}

function saveTickets(tickets) {
    localStorage.setItem('sys_tickets', JSON.stringify(tickets));
}

function getCurrentUser() {
    const user = JSON.parse(sessionStorage.getItem('sys_user'));
    if (!user && window.location.pathname.indexOf('index.html') === -1) {
        window.location.href = 'index.html'; // Força login
    }
    return user;
}

function getStatusClass(status) {
    const map = {
        "Aberto": "st-aberto",
        "Em andamento": "st-andamento",
        "Com Bloqueio": "st-bloqueio",
        "Aguardando Validação": "st-validacao",
        "Em migração": "st-migracao",
        "Concluído": "st-concluido",
        "Documentação Pendente": "st-pendente"
    };
    return map[status] || "st-aberto";
}

// --- 3. LÓGICA POR PÁGINA ---

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    // --- LOGIN ---
    if (path.includes('index.html') || path === '/') {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const role = document.getElementById('role').value;

                sessionStorage.setItem('sys_user', JSON.stringify({ email, role }));
                window.location.href = '/dashboard';
            });
        }
    }

    // --- DASHBOARD ---
    if (path.includes('dashboard.html')) {
        const user = getCurrentUser();
        document.getElementById('user-display').innerText = `${user.email} (${user.role})`;

        const tableBody = document.getElementById('ticket-table-body');
        const tickets = getTickets();

        // 1. Renderizar Tabela
        function renderTable(data) {
            tableBody.innerHTML = '';
            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px;">Nenhum chamado encontrado.</td></tr>';
                return;
            }

            data.forEach(t => {
                const tr = document.createElement('tr');
                tr.onclick = () => window.location.href = `detalhes.html?id=${t.id}`;
                tr.innerHTML = `
                    <td>#${t.id}</td>
                    <td>${t.title}</td>
                    <td>${t.category}</td>
                    <td><span class="badge ${getStatusClass(t.status)}">${t.status}</span></td>
                    <td>${t.priority || '-'}</td>
                    <td>${t.requester}</td> <td>${t.assignee || '<span style="color:#999; font-style:italic">Não atribuído</span>'}</td> `;
                tableBody.appendChild(tr);
            });
        }

        // 2. Preencher Filtros Dinamicamente (Funcional e Técnico)
        function populateFilters() {
            // Extrai lista única de Solicitantes
            const uniqueRequesters = [...new Set(tickets.map(t => t.requester))].sort();
            const reqSelect = document.getElementById('filter-requester');

            uniqueRequesters.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r;
                opt.textContent = r;
                reqSelect.appendChild(opt);
            });

            // Extrai lista única de Técnicos (removendo vazios)
            const uniqueTechs = [...new Set(tickets.map(t => t.assignee).filter(Boolean))].sort();
            const techSelect = document.getElementById('filter-assignee');

            uniqueTechs.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t;
                techSelect.appendChild(opt);
            });
        }

        // Inicializa
        populateFilters();
        renderTable(tickets);

        // 3. Lógica de Filtragem (Atualizada)
        document.getElementById('btn-filter').addEventListener('click', () => {
            const txtSearch = document.getElementById('search-text').value.toLowerCase();
            const statusFilter = document.getElementById('filter-status').value;
            const reqFilter = document.getElementById('filter-requester').value; // Novo
            const techFilter = document.getElementById('filter-assignee').value; // Novo

            const filtered = tickets.filter(t => {
                // Filtro de Texto (Título)
                const matchesText = t.title.toLowerCase().includes(txtSearch);

                // Filtro de Status
                const matchesStatus = statusFilter === "" || t.status === statusFilter;

                // Filtro de Solicitante (Funcional)
                const matchesReq = reqFilter === "" || t.requester === reqFilter;

                // Filtro de Técnico
                let matchesTech = true;
                if (techFilter === "unassigned") {
                    matchesTech = !t.assignee || t.assignee === "";
                } else if (techFilter !== "") {
                    matchesTech = t.assignee === techFilter;
                }

                return matchesText && matchesStatus && matchesReq && matchesTech;
            });

            renderTable(filtered);
        });
    }

    // --- CRIAR CHAMADO ---
    if (path.includes('criar.html')) {
        const user = getCurrentUser();
        document.getElementById('requester').value = user.email; // Auto preencher

        document.getElementById('create-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const tickets = getTickets();
            const newId = tickets.length > 0 ? Math.max(...tickets.map(t => t.id)) + 1 : 1001;

            const newTicket = {
                id: newId,
                title: document.getElementById('title').value,
                category: document.getElementById('category').value,
                status: "Aberto",
                priority: document.getElementById('priority').value,
                requester: user.email,
                assignee: "",
                description: document.getElementById('description').value,
                history: [`Criado em ${new Date().toLocaleDateString()} por ${user.email}`]
            };

            tickets.push(newTicket);
            saveTickets(tickets);
            alert('Chamado criado com sucesso!');
            window.location.href = 'dashboard.html';
        });
    }

    // --- DETALHES ---
    if (path.includes('detalhes.html')) {
        const user = getCurrentUser();
        const urlParams = new URLSearchParams(window.location.search);
        const ticketId = parseInt(urlParams.get('id'));
        const tickets = getTickets();
        const ticketIndex = tickets.findIndex(t => t.id === ticketId);

        if (ticketIndex === -1) { alert('Chamado não encontrado'); window.location.href = 'dashboard.html'; return; }

        const ticket = tickets[ticketIndex];

        // Preencher Campos
        document.getElementById('ticket-id-display').innerText = `#${ticket.id}`;
        document.getElementById('title').value = ticket.title;
        document.getElementById('category').value = ticket.category;
        document.getElementById('priority').value = ticket.priority;
        document.getElementById('description').value = ticket.description;
        document.getElementById('requester').value = ticket.requester;
        document.getElementById('status').value = ticket.status;
        document.getElementById('assignee').value = ticket.assignee;

        // Histórico
        const historyList = document.getElementById('history-list');
        ticket.history.forEach(h => {
            const li = document.createElement('li');
            li.textContent = h;
            historyList.appendChild(li);
        });

        // REGRAS DE INTERFACE
        const isTech = user.role === 'tecnico';
        const isClosed = ticket.status === 'Concluído';
        const isOpen = ticket.status === 'Aberto';

        // 1. Se não for Aberto, campos de edição (Título/Desc) desabilitados
        if (!isOpen) {
            document.getElementById('title').disabled = true;
            document.getElementById('description').disabled = true;
            document.getElementById('category').disabled = true;
            document.getElementById('priority').disabled = true;
        }

        // 2. Controle de Status e Atribuição
        if (!isTech) {
            // Usuário comum não muda status nem atribui técnico
            document.getElementById('status').disabled = true;
            document.getElementById('assignee').disabled = true;

            // Se estiver bloqueado/fechado, usuário comum só lê
            if (isClosed) {
                document.querySelector('button[type="submit"]').style.display = 'none';
            }
        }

        // Salvar Alterações
        document.getElementById('details-form').addEventListener('submit', (e) => {
            e.preventDefault();

            const newStatus = document.getElementById('status').value;
            const newAssignee = document.getElementById('assignee').value;

            // Atualizar histórico se houve mudança
            if (newStatus !== ticket.status) {
                ticket.history.push(`Status alterado de "${ticket.status}" para "${newStatus}" em ${new Date().toLocaleDateString()}`);
            }
            if (newAssignee !== ticket.assignee) {
                ticket.history.push(`Técnico atribuído: ${newAssignee}`);
            }

            // Atualiza objeto
            ticket.status = newStatus;
            ticket.assignee = newAssignee;
            // Se ainda for editável, salva dados básicos
            if (isOpen) {
                ticket.title = document.getElementById('title').value;
                ticket.description = document.getElementById('description').value;
            }

            tickets[ticketIndex] = ticket;
            saveTickets(tickets);
            alert('Chamado atualizado!');
            window.location.reload();
        });
    }

    // Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            sessionStorage.removeItem('sys_user');
            window.location.href = 'index.html';
        });
    }
});


function visualizarImagem(url, nome) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const caption = document.getElementById('modalCaption');
    
    modal.style.display = 'block';
    modalImg.src = url;
    caption.innerHTML = nome;
}

function fecharModal() {
    document.getElementById('imageModal').style.display = 'none';
}

// Fechar modal com tecla ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        fecharModal();
    }
});

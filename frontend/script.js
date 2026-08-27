const STORAGE_KEYS = {
  users: "ax_users",
  currentUser: "ax_current_user"
};

const partCatalog = {
  Hydraulics: [
    { name: "Hydraulic Pump", id: "HYD-PMP-001" },
    { name: "Control Valve", id: "HYD-VLV-014" },
    { name: "Actuator Cylinder", id: "HYD-ACT-022" }
  ],
  Electronics: [
    { name: "Sensor Module", id: "ELE-SNS-104" },
    { name: "Control Board", id: "ELE-CTL-118" },
    { name: "Power Relay", id: "ELE-RLY-133" }
  ],
  Fasteners: [
    { name: "Hex Bolt Set", id: "FST-BLT-212" },
    { name: "Lock Nut Pack", id: "FST-NUT-225" },
    { name: "Washer Kit", id: "FST-WSR-231" }
  ],
  Filtration: [
    { name: "Air Filter Cartridge", id: "FIL-AIR-309" },
    { name: "Oil Filter Unit", id: "FIL-OIL-317" },
    { name: "Dust Separator", id: "FIL-DST-324" }
  ]
};

const demoUsers = [
  {
    role: "Buyer",
    name: "Ava Buyer",
    email: "buyer@demo.com",
    password: "buyer123",
    company: "Northline Procurement",
    customerId: "CUST-BUY-1001",
    phone: "+1 555 0101",
    location: "Chicago, USA",
    preferredCategory: "Hydraulics"
  },
  {
    role: "Seller",
    name: "Noah Seller",
    email: "seller@demo.com",
    password: "seller123",
    company: "Prime Parts Supply",
    customerId: "CUST-SEL-2001",
    phone: "+1 555 0202",
    location: "Austin, USA",
    preferredCategory: "Electronics"
  }
];

function seedUsers() {
  if (!localStorage.getItem(STORAGE_KEYS.users)) {
    localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(demoUsers));
  }
}

function getUsers() {
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.users) || "[]");
}

function saveUsers(users) {
  localStorage.setItem(STORAGE_KEYS.users, JSON.stringify(users));
}

function getCurrentUser() {
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.currentUser) || "null");
}

function saveCurrentUser(user) {
  localStorage.setItem(STORAGE_KEYS.currentUser, JSON.stringify(user));
}

seedUsers();

const form = document.getElementById("order-form");
const categorySelect = document.getElementById("category");
const partNameSelect = document.getElementById("partName");
const partIdInput = document.getElementById("partId");
const customerIdInput = document.getElementById("customerId");
const statusMessage = document.getElementById("statusMessage");
const resultTableBody = document.getElementById("resultTableBody");
const requestPanel = document.getElementById("requestPanel");
const orderForm = document.getElementById("order-form");
const sellerWorkspace = document.getElementById("sellerWorkspace");
const formTitle = document.getElementById("form-title");
const formDescription = document.getElementById("form-description");
const welcomeScreen = document.getElementById("welcomeScreen");
const welcomeTitle = document.getElementById("welcomeTitle");
const welcomeContinue = document.getElementById("welcomeContinue");
const dashboardPage = document.getElementById("dashboardPage");

const authModal = document.getElementById("authModal");
const closeAuthModalButton = document.getElementById("closeAuthModal");
const roleSelection = document.getElementById("roleSelection");
const authPanel = document.getElementById("authPanel");
const authForm = document.getElementById("authForm");
const authSubmitButton = document.getElementById("authSubmitButton");
const toggleAuthModeButton = document.getElementById("toggleAuthMode");
const authError = document.getElementById("authError");
const authRoleBadge = document.getElementById("authRoleBadge");
const authModalTitle = document.getElementById("authModalTitle");
const authModalText = document.getElementById("authModalText");
const demoCredentials = document.getElementById("demoCredentials");
const authEmailInput = document.getElementById("authEmail");
const authPasswordInput = document.getElementById("authPassword");
const authNameInput = document.getElementById("authName");
const authCompanyInput = document.getElementById("authCompany");
const nameField = document.getElementById("nameField");
const companyField = document.getElementById("companyField");
const roleSelectionButtons = document.querySelectorAll("[data-role-select]");

let authState = {
  role: "Buyer",
  mode: "login"
};

const fieldConfig = [
  {
    id: "category",
    validate: (value) => value.trim() !== "",
    message: "Please select a category."
  },
  {
    id: "partName",
    validate: (value) => value.trim() !== "",
    message: "Please select a part name."
  },
  {
    id: "partId",
    validate: (value) => value.trim() !== "",
    message: "A matching part ID is required."
  },
  {
    id: "requestedQuantity",
    validate: (value) => Number.isInteger(Number(value)) && Number(value) > 0,
    message: "Requested quantity must be a positive whole number."
  },
  {
    id: "leadTime",
    validate: (value) => Number.isInteger(Number(value)) && Number(value) > 0,
    message: "Lead time must be a positive whole number of days."
  },
  {
    id: "priorityLevel",
    validate: (value) => ["Low", "Medium", "Critical"].includes(value),
    message: "Please select a priority level."
  }
];

function setFieldError(fieldId, message) {
  const input = document.getElementById(fieldId);
  const errorElement = document.getElementById(`${fieldId}Error`);

  if (input) {
    input.classList.toggle("input-error", Boolean(message));
  }

  if (errorElement) {
    errorElement.textContent = message;
  }
}

function clearErrors() {
  fieldConfig.forEach((field) => setFieldError(field.id, ""));
}

function renderPartOptions(category) {
  const parts = partCatalog[category] || [];

  partNameSelect.innerHTML = "";

  if (!parts.length) {
    partNameSelect.disabled = true;
    partNameSelect.innerHTML = '<option value="">Select category first</option>';
    partIdInput.value = "";
    return;
  }

  partNameSelect.disabled = false;
  partNameSelect.innerHTML = '<option value="">Select part name</option>';

  parts.forEach((part) => {
    const option = document.createElement("option");
    option.value = part.name;
    option.textContent = part.name;
    option.dataset.partId = part.id;
    partNameSelect.appendChild(option);
  });
}

function syncPartId() {
  const selectedOption = partNameSelect.options[partNameSelect.selectedIndex];
  partIdInput.value = selectedOption?.dataset?.partId || "";
}

function updateCustomerIdFromSession() {
  const currentUser = getCurrentUser();
  customerIdInput.value = currentUser?.customerId || "CUST-GUEST-0001";
}

function updateDashboardForRole() {
  const currentUser = getCurrentUser();
  const isSeller = currentUser?.role === "Seller";

  orderForm.hidden = isSeller;
  sellerWorkspace.hidden = !isSeller;
  requestPanel.classList.toggle("panel--seller", isSeller);
  formTitle.textContent = isSeller ? "Seller Workspace" : "New Fulfillment Request";
  formDescription.textContent = isSeller
    ? "Your account is ready for seller-side fulfillment activity."
    : "Choose a category and part name. The matching part ID is filled in automatically.";
}

function showDashboard() {
  welcomeScreen.hidden = true;
  dashboardPage.hidden = false;
  updateDashboardForRole();
}

function startWelcomeAnimation() {
  const welcomeMessage = "Welcome to Parts Investigation System";
  let messageIndex = 0;

  welcomeTitle.textContent = "Welcome!";

  const typeNextCharacter = () => {
    if (messageIndex < welcomeMessage.length) {
      welcomeTitle.textContent = welcomeMessage.slice(0, messageIndex + 1);
      messageIndex += 1;
      window.setTimeout(typeNextCharacter, messageIndex < 9 ? 95 : 62);
      return;
    }

    welcomeTitle.classList.add("welcome-screen__title--complete");
    welcomeContinue.hidden = false;
  };

  window.setTimeout(typeNextCharacter, 700);
}

function showWelcomeScreen() {
  dashboardPage.hidden = true;
  welcomeScreen.hidden = false;
  welcomeContinue.hidden = true;
  welcomeTitle.classList.remove("welcome-screen__title--complete");
  startWelcomeAnimation();
}

function buildOrderPayload(formData) {
  return {
    customerId: customerIdInput.value,
    category: formData.get("category").trim(),
    partName: formData.get("partName").trim(),
    partId: formData.get("partId").trim(),
    requestedQuantity: Number(formData.get("requestedQuantity")),
    maximumAcceptableLeadTimeDays: Number(formData.get("leadTime")),
    priorityLevel: formData.get("priorityLevel"),
    specialInstructions: formData.get("specialInstructions").trim() || "None provided"
  };
}

function validateForm(formData) {
  let isValid = true;

  fieldConfig.forEach((field) => {
    const value = formData.get(field.id) || "";
    const fieldIsValid = field.validate(value);

    if (!fieldIsValid) {
      isValid = false;
      setFieldError(field.id, field.message);
    }
  });

  return isValid;
}

function renderSummaryTable(payload) {
  const rows = [
    ["Category", payload.category],
    ["Part Name", payload.partName],
    ["Part ID", payload.partId],
    ["Requested Quantity", String(payload.requestedQuantity)],
    ["Lead Time", `${payload.maximumAcceptableLeadTimeDays} day(s)`],
    ["Priority Level", payload.priorityLevel],
    ["Special Instructions", payload.specialInstructions]
  ];

  resultTableBody.innerHTML = rows
    .map(([label, value]) => `<tr><th scope="row">${label}</th><td>${value}</td></tr>`)
    .join("");
}

function setAuthMode(mode) {
  authState.mode = mode;
  const isSignup = mode === "signup";

  authModalTitle.textContent = isSignup ? `${authState.role} Sign Up` : `${authState.role} Login`;
  authModalText.textContent = isSignup
    ? "Create a local demo account. This is stored only in the browser."
    : "Use the demo credentials below or sign up for a local account.";
  authSubmitButton.textContent = isSignup ? "Create Account" : "Login";
  toggleAuthModeButton.textContent = isSignup ? "Already registered? Login" : "New here? Sign up";
  nameField.hidden = !isSignup;
  companyField.hidden = !isSignup;
  demoCredentials.hidden = isSignup;
  authError.textContent = "";
}

function showRoleSelection() {
  authState.role = "Buyer";
  authState.mode = "login";
  roleSelection.hidden = false;
  authPanel.hidden = true;
  authRoleBadge.textContent = "Account Access";
  authModalTitle.textContent = "Choose your role";
  authModalText.textContent = "Select how you want to continue to the local demo portal.";
  authForm.reset();
  authError.textContent = "";
}

function openAuthModal(role) {
  authState.role = role;
  authRoleBadge.textContent = `${role} Access`;
  authModal.dataset.role = role.toLowerCase();
  setAuthMode("login");
  roleSelection.hidden = true;
  authPanel.hidden = false;
  authModal.hidden = false;
  document.documentElement.classList.add("modal-open");
  document.body.classList.add("modal-open");
}

function openRoleSelectionModal() {
  showRoleSelection();
  authModal.hidden = false;
  document.documentElement.classList.add("modal-open");
  document.body.classList.add("modal-open");
}

function closeAuthModal() {
  authModal.hidden = true;
  document.documentElement.classList.remove("modal-open");
  document.body.classList.remove("modal-open");
  showRoleSelection();
}

function buildProfileFromAuth(role, email, name, company) {
  const roleCode = role === "Buyer" ? "BUY" : "SEL";
  return {
    role,
    name,
    email,
    password: authPasswordInput.value,
    company,
    customerId: `CUST-${roleCode}-${Date.now().toString().slice(-4)}`,
    phone: "",
    location: "",
    preferredCategory: ""
  };
}

function handleLogin() {
  const email = authEmailInput.value.trim().toLowerCase();
  const password = authPasswordInput.value;
  const users = getUsers();

  const matchedUser = users.find(
    (user) => user.email.toLowerCase() === email && user.password === password && user.role === authState.role
  );

  if (!matchedUser) {
    authError.textContent = "Invalid login details for the selected role.";
    return;
  }

  saveCurrentUser(matchedUser);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
  statusMessage.textContent = `${matchedUser.role} logged in as ${matchedUser.name}. Customer ID is kept hidden but ready for backend payloads.`;
  statusMessage.classList.add("status-message--success");
}

function handleSignup() {
  const name = authNameInput.value.trim();
  const email = authEmailInput.value.trim().toLowerCase();
  const company = authCompanyInput.value.trim();
  const password = authPasswordInput.value;
  const users = getUsers();

  if (!name || !email || !company || !password) {
    authError.textContent = "Please complete all sign-up fields.";
    return;
  }

  const existingUser = users.find((user) => user.email.toLowerCase() === email && user.role === authState.role);

  if (existingUser) {
    authError.textContent = "An account with this email already exists for that role.";
    return;
  }

  const newUser = buildProfileFromAuth(authState.role, email, name, company);
  users.push(newUser);
  saveUsers(users);
  saveCurrentUser(newUser);
  updateCustomerIdFromSession();
  closeAuthModal();
  showDashboard();
  statusMessage.textContent = `${newUser.role} account created for ${newUser.name}. You can edit the full profile on the profile page.`;
  statusMessage.classList.add("status-message--success");
}

welcomeContinue.addEventListener("click", () => {
  openRoleSelectionModal();
});

roleSelectionButtons.forEach((button) => {
  button.addEventListener("click", () => openAuthModal(button.dataset.roleSelect));
});

closeAuthModalButton.addEventListener("click", closeAuthModal);

authModal.addEventListener("click", (event) => {
  if (event.target === authModal) {
    closeAuthModal();
  }
});

toggleAuthModeButton.addEventListener("click", () => {
  setAuthMode(authState.mode === "login" ? "signup" : "login");
});

authForm.addEventListener("submit", (event) => {
  event.preventDefault();
  authError.textContent = "";

  if (authState.mode === "login") {
    handleLogin();
    return;
  }

  handleSignup();
});

categorySelect.addEventListener("change", () => {
  renderPartOptions(categorySelect.value);
  partNameSelect.value = "";
  partIdInput.value = "";
  setFieldError("category", "");
  setFieldError("partName", "");
  setFieldError("partId", "");
});

partNameSelect.addEventListener("change", () => {
  syncPartId();
  setFieldError("partName", "");
  setFieldError("partId", "");
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  clearErrors();
  updateCustomerIdFromSession();

  const formData = new FormData(form);
  const isValid = validateForm(formData);

  if (!isValid) {
    statusMessage.textContent = "Please fix the highlighted fields and try again.";
    statusMessage.classList.remove("status-message--success");
    return;
  }

  const orderPayload = buildOrderPayload(formData);

  console.log("Order ingestion payload:", orderPayload);
  renderSummaryTable(orderPayload);

  statusMessage.textContent = "Order validated successfully. Visible table stays clean, while customer ID remains hidden inside the payload.";
  statusMessage.classList.add("status-message--success");
});

updateCustomerIdFromSession();
renderPartOptions("");

if (getCurrentUser()) {
  showDashboard();
} else {
  showWelcomeScreen();
}

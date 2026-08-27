const STORAGE_KEYS = {
  users: "ax_users",
  currentUser: "ax_current_user"
};

const demoFallbackUser = {
  role: "Buyer",
  name: "Ava Buyer",
  email: "buyer@demo.com",
  company: "Northline Procurement",
  customerId: "CUST-BUY-1001",
  phone: "+1 555 0101",
  location: "Chicago, USA",
  preferredCategory: "Hydraulics"
};

const profileForm = document.getElementById("profileForm");
const profileSummary = document.getElementById("profileSummary");
const profileStatus = document.getElementById("profileStatus");
const profileAvatar = document.getElementById("profileAvatar");
const profileDisplayName = document.getElementById("profileDisplayName");
const profileRoleLine = document.getElementById("profileRoleLine");
const profileLogout = document.getElementById("profileLogout");

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

function renderSummary(user) {
  const initials = (user.name || "A")
    .split(" ")
    .map((namePart) => namePart[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  profileAvatar.textContent = initials;
  profileDisplayName.textContent = user.name || "Your Profile";
  profileRoleLine.textContent = `${user.role || "Demo"} · ${user.company || "Independent account"}`;
  profileSummary.innerHTML = `
    <strong>${user.name}</strong> is currently signed in as <strong>${user.role}</strong>.
    Company: <strong>${user.company || "Not set"}</strong>.
  `;
}

function loadProfile() {
  const currentUser = getCurrentUser() || demoFallbackUser;

  document.getElementById("profileName").value = currentUser.name || "";
  document.getElementById("profileRole").value = currentUser.role || "";
  document.getElementById("profileEmail").value = currentUser.email || "";
  document.getElementById("profileCompany").value = currentUser.company || "";
  document.getElementById("profilePhone").value = currentUser.phone || "";
  document.getElementById("profileLocation").value = currentUser.location || "";

  renderSummary(currentUser);
}

profileForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const currentUser = getCurrentUser() || demoFallbackUser;
  const updatedUser = {
    ...currentUser,
    name: document.getElementById("profileName").value.trim(),
    email: document.getElementById("profileEmail").value.trim(),
    company: document.getElementById("profileCompany").value.trim(),
    phone: document.getElementById("profilePhone").value.trim(),
    location: document.getElementById("profileLocation").value.trim()
  };

  const users = getUsers();
  const updatedUsers = users.map((user) =>
    user.email === currentUser.email && user.role === currentUser.role ? { ...user, ...updatedUser } : user
  );

  if (!users.length) {
    updatedUsers.push(updatedUser);
  }

  saveUsers(updatedUsers);
  saveCurrentUser(updatedUser);
  renderSummary(updatedUser);

  profileStatus.textContent = "Profile saved locally. Updated values will be available to the dashboard.";
  profileStatus.classList.add("status-message--success");
});

profileLogout.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEYS.currentUser);
  window.location.href = "./index.html";
});

loadProfile();

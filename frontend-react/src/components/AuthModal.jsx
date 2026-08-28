import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { demoUsers } from "../api/client";

export default function AuthModal({ onClose }) {
  const { login, signup } = useAuth();
  const [role, setRole] = useState("Buyer");
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const isSignup = mode === "signup";

  const submit = (e) => {
    e.preventDefault();
    setError("");
    let res;
    if (isSignup) {
      res = signup({ name, email, company, password, role });
    } else {
      res = login(email, password, role);
    }
    if (res.error) setError(res.error);
    else onClose();
  };

  const autofill = (r) => {
    const demo = demoUsers.find((u) => u.role === r);
    setRole(r);
    setEmail(demo.email);
    setPassword(demo.password);
    setError("");
  };

  return (
    <div className="fixed inset-0 z-[1000] grid place-items-center p-5 bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl p-9 w-full max-w-[440px] relative shadow-2xl animate-fade-up" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-4 right-4 w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 text-xl hover:bg-red-50 hover:text-red-500 transition-all duration-150">&times;</button>
        <div className="mb-6">
          <span className="inline-flex items-center px-3 py-1 rounded-full border border-gray-200 bg-white/90 text-[11px] font-semibold tracking-widest uppercase text-gray-500 mb-3">Access</span>
          <h2 className="text-xl font-bold mb-1.5">{isSignup ? "Create Account" : "Welcome back"}</h2>
          <p className="text-sm text-gray-500">{isSignup ? "Create a local demo account." : "Sign in to your account."}</p>
        </div>

        <div>
          <div className="flex bg-gray-100 border border-gray-200 rounded-lg p-1 mb-5">
            <button type="button"
              className={`auth-role-tab ${role === "Buyer" ? "auth-role-tab--active" : ""}`}
              onClick={() => { setRole("Buyer"); setError(""); }}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>
              Buyer
            </button>
            <button type="button"
              className={`auth-role-tab ${role === "Seller" ? "auth-role-tab--active" : ""}`}
              onClick={() => { setRole("Seller"); setError(""); }}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
              Seller
            </button>
          </div>

          {!isSignup && (
            <div className="bg-gray-50 border border-gray-200/80 rounded-lg px-4 py-3 mb-5 space-y-2">
              {demoUsers.map((demo) => (
                <div key={demo.email} className="flex items-center justify-between text-xs text-gray-500">
                  <span><strong>{demo.role}:</strong> {demo.email} / {demo.password}</span>
                  <button type="button" onClick={() => autofill(demo.role)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full border border-gray-200 bg-white text-brand-500 text-[11px] font-semibold hover:bg-brand-500 hover:text-white hover:border-brand-500 transition-all duration-150">
                    Autofill
                  </button>
                </div>
              ))}
            </div>
          )}

          <form onSubmit={submit} noValidate>
            <div className="space-y-3.5">
              {isSignup && (
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-gray-700">Full Name</label>
                  <input value={name} onChange={(e) => setName(e.target.value)} type="text" placeholder="Jordan Lee"
                    className="h-11 px-3.5 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm outline-none transition-all duration-200 focus:border-brand-500 focus:ring-[3px] focus:ring-brand-500/10" />
                </div>
              )}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Email</label>
                <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="name@company.com" required
                  className="h-11 px-3.5 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm outline-none transition-all duration-200 focus:border-brand-500 focus:ring-[3px] focus:ring-brand-500/10" />
              </div>
              {isSignup && (
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-gray-700">Company</label>
                  <input value={company} onChange={(e) => setCompany(e.target.value)} type="text" placeholder="Apex Components"
                    className="h-11 px-3.5 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm outline-none transition-all duration-200 focus:border-brand-500 focus:ring-[3px] focus:ring-brand-500/10" />
                </div>
              )}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-gray-700">Password</label>
                <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Enter password" required
                  className="h-11 px-3.5 rounded-lg border-[1.5px] border-gray-200 bg-white text-sm outline-none transition-all duration-200 focus:border-brand-500 focus:ring-[3px] focus:ring-brand-500/10" />
              </div>
            </div>
            <p className="text-xs text-red-500 min-h-[1.2em] mt-3">{error}</p>
            <div className="flex gap-2.5 mt-4">
              <button type="submit" className="flex-1 h-11 rounded-full bg-brand-500 text-white font-semibold text-sm hover:bg-brand-600 transition-all duration-200">
                {isSignup ? "Create Account" : "Login"}
              </button>
              <button type="button" onClick={() => { setMode(isSignup ? "login" : "signup"); setError(""); }}
                className="h-11 px-5 rounded-full bg-transparent border border-gray-200 text-gray-500 text-sm font-medium hover:bg-gray-50 transition-all duration-200">
                {isSignup ? "Already registered? Login" : "New here? Sign up"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

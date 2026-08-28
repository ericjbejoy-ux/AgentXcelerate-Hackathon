import { useState } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import WelcomeScreen from "./components/WelcomeScreen";
import AuthModal from "./components/AuthModal";
import NewOrder from "./pages/NewOrder";
import Analytics from "./pages/Analytics";
import Inventory from "./pages/Inventory";
import History from "./pages/History";
import Info from "./pages/Info";

const PAGES = {
  order: NewOrder,
  analytics: Analytics,
  inventory: Inventory,
  history: History,
  info: Info,
};

function AppInner() {
  const { user } = useAuth();
  const [view, setView] = useState("order");
  const [showAuth, setShowAuth] = useState(false);

  if (!user) {
    return (
      <>
        <WelcomeScreen onContinue={() => setShowAuth(true)} />
        {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
      </>
    );
  }

  const isSeller = user.role === "Seller";
  const activeView = isSeller && view === "order" ? "inventory" : view;
  const Page = PAGES[activeView] || NewOrder;

  return (
    <Layout view={activeView} onNavigate={setView}>
      <Page />
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}

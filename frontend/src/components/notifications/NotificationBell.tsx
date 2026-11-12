import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Bell, CheckCheck, CloudRain, RefreshCw, Sprout, Volume2 } from "lucide-react";
import { api } from "@/services/api";
import type { NotificationItem, NotificationList } from "@/types";

const OFFLINE_CACHE_KEY = "raitha_mitra_alerts_cache_v1";

interface NotificationBellProps {
  preferredLanguage?: string;
}

export function NotificationBell({ preferredLanguage = "kn-IN" }: NotificationBellProps) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [data, setData] = useState<NotificationList>(() => {
    try {
      const raw = localStorage.getItem(OFFLINE_CACHE_KEY);
      if (raw) return JSON.parse(raw) as NotificationList;
    } catch {
      // Ignore invalid cache
    }
    return { unread_count: 0, total_count: 0, items: [] };
  });

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getNotifications(25);
      setData(res);
      try {
        localStorage.setItem(OFFLINE_CACHE_KEY, JSON.stringify(res));
      } catch {
        // Ignore storage quota errors
      }
    } catch {
      // Keep cached alerts visible cleanly when offline
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  const handleCheckNow = async () => {
    setChecking(true);
    try {
      const res = await api.checkMonitoringNow();
      setData(res);
      try {
        localStorage.setItem(OFFLINE_CACHE_KEY, JSON.stringify(res));
      } catch {
        // Ignore
      }
      // Show browser alert if farmer explicitly granted Notification permission
      if (
        typeof window !== "undefined" &&
        "Notification" in window &&
        window.Notification.permission === "granted"
      ) {
        const urgent = res.items.find((n) => !n.is_read && (n.priority === "critical" || n.priority === "high"));
        if (urgent) {
          const isKn = preferredLanguage === "kn-IN";
          new window.Notification(isKn ? urgent.title_kn : urgent.title_en, {
            body: isKn ? urgent.message_kn : urgent.message_en,
            icon: "/assets/raithamitra-logo.png",
          });
        }
      }
    } catch {
      // Ignore silently on network issue
    } finally {
      setChecking(false);
    }
  };

  const handleEnablePush = async () => {
    if (typeof window !== "undefined" && "Notification" in window) {
      await window.Notification.requestPermission();
    }
  };

  const handleSpeakAlert = (item: NotificationItem) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const isKn = preferredLanguage === "kn-IN";
    const utter = new SpeechSynthesisUtterance(
      isKn ? `${item.title_kn}. ${item.message_kn}` : `${item.title_en}. ${item.message_en}`
    );
    utter.lang = isKn ? "kn-IN" : "en-IN";
    window.speechSynthesis.speak(utter);
  };

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setData((prev) => {
        const items = prev.items.map((n) => (n.id === id ? { ...n, is_read: true } : n));
        return {
          ...prev,
          unread_count: items.filter((n) => !n.is_read).length,
          items,
        };
      });
    } catch {
      // Ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setData((prev) => ({
        ...prev,
        unread_count: 0,
        items: prev.items.map((n) => ({ ...n, is_read: true })),
      }));
    } catch {
      // Ignore
    }
  };

  const priorityBadge = (priority: string) => {
    if (priority === "critical") return "bg-[#FCECEC] text-[#D9534F] border-[#F5C6C5]";
    if (priority === "high") return "bg-[#FEF6E6] text-[#B27700] border-[#F5DAA0]";
    return "bg-[#EDF5E9] text-[#176B35] border-[#CFE4C8]";
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => {
          setOpen((v) => !v);
          if (!open) void loadNotifications();
        }}
        className="relative p-2 rounded-xl border border-[#E6EBE2] bg-white hover:bg-[#EDF5E9] text-[#202820] transition"
        aria-label="Farm & weather notifications"
      >
        <Bell className="w-5 h-5 text-[#176B35]" />
        {data.unread_count > 0 && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[20px] h-5 px-1 rounded-full bg-[#D9534F] text-white text-[10px] font-bold flex items-center justify-center">
            {data.unread_count > 9 ? "9+" : data.unread_count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-[340px] sm:w-[400px] rounded-2xl bg-white border border-[#DCE8D8] shadow-xl z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-[#E6EBE2] bg-[#FAF9F2] flex items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-[#202820]">Smart Farm Alerts</h3>
              <p className="text-[11px] text-[#718071]">
                {data.unread_count} unread • Cached for offline access
              </p>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleCheckNow}
                disabled={checking}
                className="px-2.5 py-1.5 rounded-lg bg-[#176B35] text-white text-[11px] font-medium flex items-center gap-1 hover:bg-[#104B29]"
                title="Run weather & harvest alert check now"
              >
                <RefreshCw className={`w-3 h-3 ${checking ? "animate-spin" : ""}`} />
                Check
              </button>
              {data.unread_count > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  className="p-1.5 rounded-lg border border-[#DCE8D8] bg-white hover:bg-[#EDF5E9] text-[#176B35]"
                  title="Mark all as read"
                >
                  <CheckCheck className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto divide-y divide-[#EDF1EA]">
            {loading && data.items.length === 0 ? (
              <div className="p-4 text-xs text-[#718071] text-center">Loading alerts...</div>
            ) : data.items.length === 0 ? (
              <div className="p-5 text-center space-y-2">
                <p className="text-xs font-medium text-[#202820]">No active weather or harvest alerts yet.</p>
                <p className="text-[11px] text-[#718071]">
                  Click Check to scan live weather & tracked crop stages for your farm location.
                </p>
              </div>
            ) : (
              data.items.slice(0, 6).map((item) => {
                const isKn = preferredLanguage === "kn-IN";
                return (
                  <div
                    key={item.id}
                    className={`p-3.5 space-y-1.5 ${item.is_read ? "bg-white" : "bg-[#FAF9F2]"}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border uppercase ${priorityBadge(
                          item.priority
                        )}`}
                      >
                        {item.category.replace(/_/g, " ")}
                      </span>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleSpeakAlert(item)}
                          className="p-1 rounded hover:bg-[#EDF5E9] text-[#176B35]"
                          title="Read alert aloud"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                        </button>
                        {!item.is_read && (
                          <button
                            type="button"
                            onClick={() => handleMarkRead(item.id)}
                            className="text-[11px] text-[#176B35] font-medium hover:underline"
                          >
                            Mark read
                          </button>
                        )}
                      </div>
                    </div>

                    <p className="text-xs font-semibold text-[#202820]">
                      {isKn ? item.title_kn : item.title_en}
                    </p>
                    <p className="text-xs text-[#718071] leading-relaxed">
                      {isKn ? item.message_kn : item.message_en}
                    </p>
                    {(item.crop_name || item.growth_stage || item.recommendation_en) && (
                      <div className="rounded-lg bg-[#EDF5E9]/70 px-2.5 py-1.5 text-[11px] text-[#202820] space-y-0.5">
                        {item.crop_name && (
                          <p>
                            <strong>Crop:</strong> {item.crop_name}
                            {item.growth_stage ? ` • Stage: ${item.growth_stage}` : ""}
                          </p>
                        )}
                        {(isKn ? item.recommendation_kn : item.recommendation_en) && (
                          <p>
                            <strong>Action:</strong>{" "}
                            {isKn ? item.recommendation_kn || item.recommendation_en : item.recommendation_en}
                          </p>
                        )}
                      </div>
                    )}
                    {isKn && item.title_en && (
                      <p className="text-[11px] text-[#718071]/80 italic">{item.title_en}</p>
                    )}
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <button
                        type="button"
                        onClick={() => {
                          setOpen(false);
                          navigate("/weather");
                        }}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-md border border-[#DCE8D8] bg-white hover:bg-[#EDF5E9] text-[10px] font-semibold text-[#176B35]"
                      >
                        <CloudRain className="w-3 h-3" /> View Weather
                      </button>
                      {(item.crop_id || item.crop_name || item.category === "harvest_reminder") && (
                        <button
                          type="button"
                          onClick={() => {
                            setOpen(false);
                            navigate(item.category === "harvest_reminder" ? "/harvest" : "/growth");
                          }}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded-md border border-[#DCE8D8] bg-white hover:bg-[#EDF5E9] text-[10px] font-semibold text-[#176B35]"
                        >
                          <Sprout className="w-3 h-3" /> View Crop
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="px-4 py-2.5 border-t border-[#E6EBE2] bg-[#FAF9F2] flex items-center justify-between text-xs">
            <button
              type="button"
              onClick={handleEnablePush}
              className="text-[#718071] hover:text-[#176B35] font-medium"
            >
              Enable Browser Alerts
            </button>
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="font-semibold text-[#176B35] hover:underline"
            >
              View All Alerts →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

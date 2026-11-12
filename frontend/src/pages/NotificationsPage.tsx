import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bell, CheckCheck, CloudRain, RefreshCw, ShieldCheck, Sprout, Volume2 } from "lucide-react";
import { CardSkeleton, EmptyState, ErrorState, SuccessBanner } from "@/components/common/StateFeedback";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { api } from "@/services/api";
import type { NotificationItem, NotificationList } from "@/types";

export const NotificationsPage: React.FC = () => {
  const { farmer } = useAuth();
  const { language } = useLanguage();
  const isKn = (farmer?.preferred_language || language) === "kn-IN";

  const [data, setData] = useState<NotificationList | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const loadList = () => {
    setLoading(true);
    api
      .getNotifications(100)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load notifications"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadList();
  }, []);

  const handleCheckNow = async () => {
    setChecking(true);
    setError(null);
    setInfo(null);
    try {
      const res = await api.checkMonitoringNow();
      setData(res);
      setInfo("Completed live weather, flood, and crop stage check for your farm.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Alert check failed");
    } finally {
      setChecking(false);
    }
  };

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      loadList();
    } catch {
      // Ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      loadList();
    } catch {
      // Ignore
    }
  };

  const handleSpeak = (n: NotificationItem) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(
      isKn ? `${n.title_kn}. ${n.message_kn}` : `${n.title_en}. ${n.message_en}`
    );
    utter.lang = isKn ? "kn-IN" : "en-IN";
    window.speechSynthesis.speak(utter);
  };

  const categories = Array.from(new Set((data?.items || []).map((i) => i.category)));
  const visibleItems = (data?.items || []).filter(
    (item) => filterCategory === "all" || item.category === filterCategory
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-deep">Smart Weather & Crop Alert Center</h1>
          <p className="text-sm text-muted mt-1">
            Automated bilingual Kannada & English alerts for rainfall, official flood warnings, irrigation pauses, wind stress, and harvest windows.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={handleCheckNow} disabled={checking} className="rm-btn-primary">
            <RefreshCw className={`h-4 w-4 ${checking ? "animate-spin" : ""}`} />
            {checking ? "Scanning Weather & Crops..." : "Check Farm Alerts Now"}
          </button>
          {data && data.unread_count > 0 && (
            <button type="button" onClick={handleMarkAllRead} className="rm-btn-secondary">
              <CheckCheck className="h-4 w-4" />
              Mark All Read ({data.unread_count})
            </button>
          )}
        </div>
      </div>

      {info && <SuccessBanner message={info} />}
      {error && <ErrorState message={error} onRetry={loadList} />}

      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setFilterCategory("all")}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
              filterCategory === "all"
                ? "bg-forest text-white border-forest"
                : "bg-white text-ink border-[#DCE8D8] hover:bg-mint"
            }`}
          >
            All ({data?.total_count || 0})
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border capitalize transition ${
                filterCategory === cat
                  ? "bg-forest text-white border-forest"
                  : "bg-white text-ink border-[#DCE8D8] hover:bg-mint"
              }`}
            >
              {cat.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      )}

      {loading && !data ? (
        <div className="space-y-3">
          <CardSkeleton lines={3} />
          <CardSkeleton lines={3} />
        </div>
      ) : visibleItems.length === 0 ? (
        <EmptyState
          title="No alerts match right now"
          description="Click Check Farm Alerts Now to scan today's live weather forecast and active crop stages."
        />
      ) : (
        <div className="space-y-3">
          {visibleItems.map((n) => (
            <div
              key={n.id}
              className={`rm-card p-5 space-y-2.5 ${
                n.is_read ? "opacity-90" : "border-l-4 border-l-forest bg-[#FAF9F2]"
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-forest" />
                  <span className="rounded-full bg-mint px-2.5 py-0.5 text-[11px] font-bold uppercase text-forest">
                    {n.category.replace(/_/g, " ")}
                  </span>
                  <span className="text-[11px] font-semibold uppercase text-muted">
                    {n.priority}
                  </span>
                  {n.alert_type_label === "official_flood_warning" && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-[#FCECEC] text-[#D9534F] px-2 py-0.5 text-[10px] font-bold">
                      <ShieldCheck className="h-3 w-3" /> Official Feed
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleSpeak(n)}
                    className="rm-btn-secondary !py-1 !px-2.5 text-xs"
                  >
                    <Volume2 className="h-3.5 w-3.5" />
                    Speak
                  </button>
                  {!n.is_read && (
                    <button
                      type="button"
                      onClick={() => void handleMarkRead(n.id)}
                      className="text-xs font-semibold text-forest hover:underline"
                    >
                      Mark Read
                    </button>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold text-deep">{n.title_kn}</h3>
                <p className="text-xs font-semibold text-ink mt-0.5">{n.title_en}</p>
              </div>
              <p className="text-xs text-deep leading-relaxed">{n.message_kn}</p>
              <p className="text-xs text-muted leading-relaxed">{n.message_en}</p>

              {(n.crop_name || n.growth_stage || n.recommendation_en || n.recommendation_kn) && (
                <div className="rounded-xl bg-[#EDF5E9]/70 border border-[#CFE4C8] p-3 text-xs space-y-1">
                  {n.crop_name && (
                    <p className="text-deep">
                      <strong>Crop:</strong> {n.crop_name}
                      {n.growth_stage ? ` • Growth stage: ${n.growth_stage}` : ""}
                    </p>
                  )}
                  {(n.recommendation_kn || n.recommendation_en) && (
                    <p className="text-ink">
                      <strong>Recommendation:</strong> {isKn ? n.recommendation_kn || n.recommendation_en : n.recommendation_en}
                    </p>
                  )}
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <p className="text-[11px] text-muted">
                  Source: {n.source_name} • {new Date(n.created_at).toLocaleString()}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    to="/weather"
                    className="rm-btn-secondary !py-1.5 !px-3 text-xs inline-flex items-center gap-1"
                  >
                    <CloudRain className="h-3.5 w-3.5" />
                    View Weather
                  </Link>
                  <Link
                    to={n.category === "harvest_reminder" ? "/harvest" : "/growth"}
                    className="rm-btn-secondary !py-1.5 !px-3 text-xs inline-flex items-center gap-1"
                  >
                    <Sprout className="h-3.5 w-3.5" />
                    View Crop
                  </Link>
                  {!n.is_read && (
                    <button
                      type="button"
                      onClick={() => void handleMarkRead(n.id)}
                      className="rm-btn-primary !py-1.5 !px-3 text-xs"
                    >
                      Mark as Read
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

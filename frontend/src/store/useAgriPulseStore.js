import { create } from "zustand";
import { useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api.js";

export const useAgriPulseStore = create((set) => ({
  currentPage: "landing",
  farm: null,
  farmId: null,
  report: null,
  loading: false,
  error: null,
  askAnswer: null,
  MapsTo: (page) => set({ currentPage: page }),
  getStarted: () => set({ currentPage: "dashboard" }),
  actions: {
    generateReport: () =>
      set({
        loading: true,
        error: null,
        report: null,
        farm: null,
        farmId: null,
        askAnswer: null,
      }),
    askQuestion: () => set({ loading: true, error: null, askAnswer: null }),
    reset: () =>
      set({
        farm: null,
        farmId: null,
        report: null,
        loading: false,
        error: null,
        askAnswer: null,
      }),
  },
}));

const setReportState = (report) =>
  useAgriPulseStore.setState({ report, loading: false, error: null });
const setFarmState = (farm) =>
  useAgriPulseStore.setState({ farm, farmId: farm.farm_id });
const setErrorState = (error) =>
  useAgriPulseStore.setState({ loading: false, error: error.message });
const setAnswerState = (askAnswer) =>
  useAgriPulseStore.setState({ askAnswer, loading: false, error: null });

export function useReportWorkflow() {
  const actions = useAgriPulseStore((state) => state.actions);
  const farmId = useAgriPulseStore((state) => state.farmId);
  const reportQuery = useQuery({
    queryKey: ["intelligence", farmId],
    queryFn: () => api.getIntelligence(farmId),
    enabled: Boolean(farmId),
    retry: false,
  });
  const createFarmMutation = useMutation({
    mutationFn: api.createFarm,
    retry: false,
    onSuccess: setFarmState,
    onError: setErrorState,
  });

  const generateReport = (formData) => {
    actions.generateReport(formData);
    createFarmMutation.mutate(formData);
  };

  useEffect(() => {
    if (reportQuery.data) setReportState(reportQuery.data);
    if (reportQuery.error) setErrorState(reportQuery.error);
  }, [reportQuery.data, reportQuery.error]);

  return {
    generateReport,
    loading: createFarmMutation.isPending || reportQuery.isFetching,
  };
}

export function useAskWorkflow() {
  const actions = useAgriPulseStore((state) => state.actions);
  const farmId = useAgriPulseStore((state) => state.farmId);
  const askMutation = useMutation({
    mutationFn: (question) => api.ask(farmId, question),
    retry: 1,
    onSuccess: setAnswerState,
    onError: setErrorState,
  });

  const askQuestion = (question) => {
    actions.askQuestion(question);
    askMutation.mutate(question);
  };

  return { askQuestion, loading: askMutation.isPending };
}

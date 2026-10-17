{{- define "pantrypal.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "pantrypal.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/part-of: pantrypal
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* selector labels: call with (dict "ctx" $ "component" "backend") */}}
{{- define "pantrypal.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pantrypal.fullname" .ctx }}-{{ .component }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "pantrypal.dbSecretName" -}}
{{- if .Values.postgresql.existingSecret -}}
{{- .Values.postgresql.existingSecret -}}
{{- else -}}
{{- include "pantrypal.fullname" . }}-db
{{- end -}}
{{- end -}}

{{- define "pantrypal.dbHost" -}}
{{- if .Values.postgresql.enabled -}}
{{- include "pantrypal.fullname" . }}-postgresql
{{- else -}}
{{- required "externalDatabase.host is required when postgresql.enabled=false" .Values.externalDatabase.host -}}
{{- end -}}
{{- end -}}

{{- define "pantrypal.image" -}}
{{- $tag := required (printf "%s.image.tag must be set (use the Git commit SHA)" .component) .image.tag -}}
{{- printf "%s:%s" .image.repository $tag -}}
{{- end -}}

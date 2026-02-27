"""
Agrupamiento plano para enrutado clinico (k-means + EM opcional).

Objetivo:
- descubrir vecindades semanticas entre dominios sin etiquetas manuales extra
- reducir espacio candidato de dominio en consultas ambiguas
- exponer metricas de calidad de clustering para auditoria operativa
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from app.core.config import settings


class ClinicalFlatClusteringService:
    """Servicio de clustering plano para priorizacion de dominios clinicos."""

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)
    _QUERY_SOFTMAX_SCALE = 4.0
    _EM_DISTANCE_SCALE = 6.0

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(text or ""))
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        return [token for token in cls._TOKEN_PATTERN.findall(cls._normalize(text))]

    @staticmethod
    def _safe_div(num: float, den: float) -> float:
        return float(num) / float(den) if den else 0.0

    @staticmethod
    def _dot(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(float(value) * float(right.get(term, 0.0)) for term, value in left.items())

    @staticmethod
    def _l2_normalize(vector: dict[str, float]) -> dict[str, float]:
        if not vector:
            return {}
        norm = math.sqrt(sum(float(value) ** 2 for value in vector.values()))
        if norm <= 0:
            return {}
        return {term: float(value) / norm for term, value in vector.items()}

    @staticmethod
    def _softmax(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}
        max_score = max(scores.values())
        exps = {label: math.exp(score - max_score) for label, score in scores.items()}
        denom = sum(exps.values()) or 1.0
        return {label: value / denom for label, value in exps.items()}

    @staticmethod
    def _entropy(probabilities: dict[str, float]) -> float:
        entropy = 0.0
        for value in probabilities.values():
            if value <= 0:
                continue
            entropy -= float(value) * math.log(float(value))
        return entropy

    @classmethod
    def _build_training_samples(
        cls,
        *,
        domain_catalog: list[dict[str, object]],
    ) -> list[tuple[str, list[str]]]:
        samples: list[tuple[str, list[str]]] = []
        for item in domain_catalog:
            label = str(item.get("key") or "").strip()
            if not label:
                continue
            title = str(item.get("label") or "")
            summary = str(item.get("summary") or "")
            keywords = [str(token) for token in (item.get("keywords") or [])]
            keyword_text = " ".join(keywords)
            sample_texts = [
                f"{label} {title} {summary}",
                keyword_text,
                f"{title} {keyword_text}",
            ]
            for text in sample_texts:
                tokens = cls._tokenize(text)
                if tokens:
                    samples.append((label, tokens))
        return samples

    @classmethod
    def _compute_idf(
        cls,
        *,
        samples: list[tuple[str, list[str]]],
    ) -> dict[str, float]:
        if not samples:
            return {}
        doc_count = len(samples)
        df = Counter()
        for _, tokens in samples:
            for term in set(tokens):
                df[term] += 1
        return {
            term: math.log((1.0 + float(doc_count)) / (1.0 + float(freq))) + 1.0
            for term, freq in df.items()
        }

    @classmethod
    def _vectorize_tokens(
        cls,
        *,
        tokens: list[str],
        idf: dict[str, float],
    ) -> dict[str, float]:
        if not tokens or not idf:
            return {}
        tf = Counter(token for token in tokens if token in idf)
        weighted = {
            term: (1.0 + math.log(float(freq))) * float(idf.get(term, 0.0))
            for term, freq in tf.items()
            if freq > 0
        }
        return cls._l2_normalize(weighted)

    @classmethod
    def _distance_sq(
        cls,
        *,
        left: dict[str, float],
        right: dict[str, float],
        left_norm: float | None = None,
        right_norm: float | None = None,
    ) -> float:
        ln = float(left_norm) if left_norm is not None else sum(v * v for v in left.values())
        rn = float(right_norm) if right_norm is not None else sum(v * v for v in right.values())
        dist = ln + rn - (2.0 * cls._dot(left, right))
        return max(0.0, dist)

    @classmethod
    def _init_centroids(
        cls,
        *,
        vectors: list[dict[str, float]],
        k: int,
    ) -> list[dict[str, float]]:
        n = len(vectors)
        if n == 0:
            return []
        k = max(1, min(k, n))
        if k == 1:
            return [dict(vectors[0])]

        # Inicializacion determinista (sin random) para estabilidad de tests.
        indices: list[int] = []
        for i in range(k):
            index = int((i * n) / k)
            if index >= n:
                index = n - 1
            if index not in indices:
                indices.append(index)
        for index in range(n):
            if len(indices) >= k:
                break
            if index not in indices:
                indices.append(index)
        return [dict(vectors[index]) for index in indices[:k]]

    @classmethod
    def _mean_vector(
        cls,
        *,
        vectors: list[dict[str, float]],
        weights: list[float] | None = None,
    ) -> dict[str, float]:
        if not vectors:
            return {}
        sums: dict[str, float] = defaultdict(float)
        if weights is None:
            weights = [1.0] * len(vectors)
        total_weight = 0.0
        for vector, weight in zip(vectors, weights, strict=True):
            if weight <= 0:
                continue
            total_weight += float(weight)
            for term, value in vector.items():
                sums[term] += float(value) * float(weight)
        if total_weight <= 0:
            return {}
        averaged = {term: float(value) / total_weight for term, value in sums.items()}
        return cls._l2_normalize(averaged)

    @classmethod
    def _run_kmeans(
        cls,
        *,
        vectors: list[dict[str, float]],
        k: int,
        max_iterations: int,
    ) -> dict[str, Any]:
        n = len(vectors)
        if n == 0:
            return {
                "centroids": [],
                "assignments": [],
                "rss": 0.0,
                "iterations": 0,
            }
        centroids = cls._init_centroids(vectors=vectors, k=k)
        k = len(centroids)
        assignments = [-1] * n
        vector_norms = [sum(v * v for v in vector.values()) for vector in vectors]

        for iteration in range(max(1, max_iterations)):
            changed = False
            centroid_norms = [sum(v * v for v in centroid.values()) for centroid in centroids]
            cluster_members: list[list[int]] = [[] for _ in range(k)]

            for index, vector in enumerate(vectors):
                best_cluster = 0
                best_dist = float("inf")
                for cluster_id, centroid in enumerate(centroids):
                    dist = cls._distance_sq(
                        left=vector,
                        right=centroid,
                        left_norm=vector_norms[index],
                        right_norm=centroid_norms[cluster_id],
                    )
                    if dist < best_dist:
                        best_dist = dist
                        best_cluster = cluster_id
                cluster_members[best_cluster].append(index)
                if assignments[index] != best_cluster:
                    assignments[index] = best_cluster
                    changed = True

            new_centroids: list[dict[str, float]] = []
            for cluster_id, members in enumerate(cluster_members):
                if not members:
                    new_centroids.append(dict(centroids[cluster_id]))
                    continue
                cluster_vectors = [vectors[index] for index in members]
                new_centroids.append(cls._mean_vector(vectors=cluster_vectors))
            centroids = new_centroids

            if not changed:
                break

        centroid_norms = [sum(v * v for v in centroid.values()) for centroid in centroids]
        rss = 0.0
        for index, vector in enumerate(vectors):
            cluster_id = assignments[index]
            rss += cls._distance_sq(
                left=vector,
                right=centroids[cluster_id],
                left_norm=vector_norms[index],
                right_norm=centroid_norms[cluster_id],
            )

        return {
            "centroids": centroids,
            "assignments": assignments,
            "rss": float(rss),
            "iterations": int(iteration + 1),
        }

    @classmethod
    def _run_em_refinement(
        cls,
        *,
        vectors: list[dict[str, float]],
        initial_centroids: list[dict[str, float]],
        max_iterations: int,
    ) -> dict[str, Any]:
        n = len(vectors)
        k = len(initial_centroids)
        if n == 0 or k == 0:
            return {
                "centroids": initial_centroids,
                "assignments": [],
                "responsibilities": [],
                "iterations": 0,
            }

        centroids = [dict(item) for item in initial_centroids]
        responsibilities = [[0.0 for _ in range(k)] for _ in range(n)]
        vector_norms = [sum(v * v for v in vector.values()) for vector in vectors]

        for iteration in range(max(1, max_iterations)):
            centroid_norms = [sum(v * v for v in centroid.values()) for centroid in centroids]

            # E-step: asignacion blanda por distancia a centroides.
            for row_id, vector in enumerate(vectors):
                scores: list[float] = []
                for cluster_id, centroid in enumerate(centroids):
                    dist = cls._distance_sq(
                        left=vector,
                        right=centroid,
                        left_norm=vector_norms[row_id],
                        right_norm=centroid_norms[cluster_id],
                    )
                    scores.append(math.exp(-cls._EM_DISTANCE_SCALE * dist))
                denom = sum(scores) or 1.0
                responsibilities[row_id] = [float(score) / denom for score in scores]

            # M-step: centroides por media ponderada de responsabilidades.
            new_centroids: list[dict[str, float]] = []
            for cluster_id in range(k):
                weights = [responsibilities[row_id][cluster_id] for row_id in range(n)]
                new_centroids.append(cls._mean_vector(vectors=vectors, weights=weights))

            # Criterio de parada por desplazamiento de centroides.
            shift = 0.0
            for current, updated in zip(centroids, new_centroids, strict=True):
                shift += cls._distance_sq(left=current, right=updated)
            centroids = new_centroids
            if shift <= 1e-6:
                break

        assignments = [
            int(max(range(k), key=lambda cluster_id: responsibilities[row_id][cluster_id]))
            for row_id in range(n)
        ]
        return {
            "centroids": centroids,
            "assignments": assignments,
            "responsibilities": responsibilities,
            "iterations": int(iteration + 1),
        }

    @classmethod
    def _evaluate_clustering(
        cls,
        *,
        true_labels: list[str],
        cluster_ids: list[int],
        beta: float,
    ) -> dict[str, float]:
        if not true_labels or len(true_labels) != len(cluster_ids):
            return {
                "purity": 0.0,
                "nmi": 0.0,
                "rand_index": 0.0,
                "f_measure": 0.0,
            }

        n = len(true_labels)
        class_labels = sorted(set(true_labels))
        clusters = sorted(set(int(item) for item in cluster_ids))
        class_index = {label: idx for idx, label in enumerate(class_labels)}
        cluster_index = {cluster: idx for idx, cluster in enumerate(clusters)}

        contingency = [
            [0 for _ in range(len(class_labels))]
            for _ in range(len(clusters))
        ]
        for label, cluster_id in zip(true_labels, cluster_ids, strict=True):
            contingency[cluster_index[int(cluster_id)]][class_index[label]] += 1

        cluster_totals = [sum(row) for row in contingency]
        class_totals = [
            sum(contingency[row_id][col_id] for row_id in range(len(clusters)))
            for col_id in range(len(class_labels))
        ]

        purity = cls._safe_div(sum(max(row) if row else 0 for row in contingency), n)

        mutual_info = 0.0
        for row_id, row in enumerate(contingency):
            for col_id, count in enumerate(row):
                if count <= 0:
                    continue
                p_joint = float(count) / float(n)
                p_cluster = cls._safe_div(cluster_totals[row_id], n)
                p_class = cls._safe_div(class_totals[col_id], n)
                if p_cluster > 0 and p_class > 0:
                    mutual_info += p_joint * math.log(p_joint / (p_cluster * p_class))

        h_cluster = 0.0
        for total in cluster_totals:
            p = cls._safe_div(total, n)
            if p > 0:
                h_cluster -= p * math.log(p)
        h_class = 0.0
        for total in class_totals:
            p = cls._safe_div(total, n)
            if p > 0:
                h_class -= p * math.log(p)
        nmi = cls._safe_div(mutual_info, (h_cluster + h_class) / 2.0)

        tp = fp = fn = tn = 0
        for left in range(n):
            for right in range(left + 1, n):
                same_class = true_labels[left] == true_labels[right]
                same_cluster = int(cluster_ids[left]) == int(cluster_ids[right])
                if same_class and same_cluster:
                    tp += 1
                elif same_cluster and not same_class:
                    fp += 1
                elif same_class and not same_cluster:
                    fn += 1
                else:
                    tn += 1
        rand_index = cls._safe_div(tp + tn, tp + fp + fn + tn)

        beta_sq = float(beta) ** 2
        f_total = 0.0
        for col_id, class_label in enumerate(class_labels):
            class_size = class_totals[col_id]
            if class_size <= 0:
                continue
            best_f = 0.0
            for row_id, cluster_id in enumerate(clusters):
                intersection = contingency[row_id][col_id]
                if intersection <= 0:
                    continue
                precision = cls._safe_div(intersection, cluster_totals[row_id])
                recall = cls._safe_div(intersection, class_size)
                denom = (beta_sq * precision) + recall
                f_score = cls._safe_div((1.0 + beta_sq) * precision * recall, denom)
                if f_score > best_f:
                    best_f = f_score
            f_total += cls._safe_div(class_size, n) * best_f

        return {
            "purity": round(max(0.0, min(1.0, purity)), 4),
            "nmi": round(max(0.0, min(1.0, nmi)), 4),
            "rand_index": round(max(0.0, min(1.0, rand_index)), 4),
            "f_measure": round(max(0.0, min(1.0, f_total)), 4),
        }

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        domain_catalog: list[dict[str, object]],
        matched_domains: list[str],
        effective_specialty: str,  # noqa: ARG003 - reservado para calibraciones futuras
    ) -> dict[str, Any]:
        method = str(settings.CLINICAL_CHAT_CLUSTER_METHOD).strip().lower()
        k_min = int(settings.CLINICAL_CHAT_CLUSTER_K_MIN)
        k_max = int(settings.CLINICAL_CHAT_CLUSTER_K_MAX)
        max_iterations = int(settings.CLINICAL_CHAT_CLUSTER_MAX_ITERATIONS)
        em_iterations = int(settings.CLINICAL_CHAT_CLUSTER_EM_ITERATIONS)
        f_beta = float(settings.CLINICAL_CHAT_CLUSTER_F_BETA)

        disabled_payload = {
            "enabled": False,
            "method": method,
            "k_selected": 0,
            "top_cluster_id": -1,
            "top_confidence": 0.0,
            "margin_top2": 0.0,
            "entropy": 0.0,
            "candidate_domains": [],
            "singleton_clusters": [],
            "quality": {
                "purity": 0.0,
                "nmi": 0.0,
                "rand_index": 0.0,
                "f_measure": 0.0,
            },
            "trace": {
                "cluster_enabled": "0",
                "cluster_method": method,
                "cluster_k_selected": "0",
                "cluster_k_min": str(k_min),
                "cluster_k_max": str(k_max),
                "cluster_top_id": "-1",
                "cluster_top_confidence": "0.0",
                "cluster_margin_top2": "0.0",
                "cluster_entropy": "0.0",
                "cluster_candidate_domains": "none",
                "cluster_singletons": "0",
                "cluster_rss": "0.0",
                "cluster_aic": "0.0",
                "cluster_purity": "0.0",
                "cluster_nmi": "0.0",
                "cluster_rand_index": "0.0",
                "cluster_f_measure": "0.0",
                "cluster_vocab_size": "0",
                "cluster_training_docs": "0",
                "cluster_rerank_recommended": "0",
            },
            "memory_facts": [],
        }
        if not settings.CLINICAL_CHAT_CLUSTER_ENABLED:
            return disabled_payload

        samples = cls._build_training_samples(domain_catalog=domain_catalog)
        if not samples:
            return disabled_payload

        idf = cls._compute_idf(samples=samples)
        sample_vectors = [cls._vectorize_tokens(tokens=tokens, idf=idf) for _, tokens in samples]
        sample_labels = [label for label, _ in samples]
        n_samples = len(sample_vectors)
        if n_samples == 0:
            return disabled_payload

        effective_k_min = max(1, min(k_min, n_samples))
        effective_k_max = max(effective_k_min, min(k_max, n_samples))
        candidate_ks = list(range(effective_k_min, effective_k_max + 1))

        best_run: dict[str, Any] | None = None
        best_aic = float("inf")
        for k in candidate_ks:
            kmeans_run = cls._run_kmeans(
                vectors=sample_vectors,
                k=k,
                max_iterations=max_iterations,
            )
            rss = float(kmeans_run["rss"])
            aic = rss + (2.0 * float(len(idf)) * float(k))
            if aic < best_aic:
                best_aic = aic
                best_run = {
                    "k": k,
                    "rss": rss,
                    "aic": aic,
                    "centroids": kmeans_run["centroids"],
                    "assignments": kmeans_run["assignments"],
                    "iterations": kmeans_run["iterations"],
                }

        if best_run is None:
            return disabled_payload

        assignments = list(best_run["assignments"])
        centroids = list(best_run["centroids"])
        if method == "kmeans_em":
            em_run = cls._run_em_refinement(
                vectors=sample_vectors,
                initial_centroids=centroids,
                max_iterations=em_iterations,
            )
            centroids = list(em_run["centroids"])
            assignments = list(em_run["assignments"])

        query_tokens = cls._tokenize(query)
        query_vector = cls._vectorize_tokens(tokens=query_tokens, idf=idf)
        query_norm = sum(value * value for value in query_vector.values())
        centroid_scores: dict[str, float] = {}
        centroid_distances: dict[int, float] = {}
        for cluster_id, centroid in enumerate(centroids):
            centroid_norm = sum(value * value for value in centroid.values())
            dist = cls._distance_sq(
                left=query_vector,
                right=centroid,
                left_norm=query_norm,
                right_norm=centroid_norm,
            )
            centroid_distances[cluster_id] = float(dist)
            centroid_scores[str(cluster_id)] = -float(dist) * cls._QUERY_SOFTMAX_SCALE
        cluster_probabilities = cls._softmax(centroid_scores)
        ranked_clusters = sorted(
            (
                (int(cluster_id), probability)
                for cluster_id, probability in cluster_probabilities.items()
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        top_cluster_id = ranked_clusters[0][0] if ranked_clusters else -1
        top_confidence = float(ranked_clusters[0][1]) if ranked_clusters else 0.0
        second_confidence = float(ranked_clusters[1][1]) if len(ranked_clusters) > 1 else 0.0
        margin_top2 = max(0.0, top_confidence - second_confidence)
        entropy = cls._entropy(cluster_probabilities)

        # Dominios candidatos del cluster top ordenados por similitud media a la consulta.
        domain_scores: dict[str, float] = defaultdict(float)
        domain_hits: dict[str, int] = defaultdict(int)
        for row_id, cluster_id in enumerate(assignments):
            if int(cluster_id) != int(top_cluster_id):
                continue
            label = sample_labels[row_id]
            similarity = cls._dot(query_vector, sample_vectors[row_id])
            domain_scores[label] += max(0.0, float(similarity))
            domain_hits[label] += 1
        for label, hits in domain_hits.items():
            # Penalizacion leve por escasez de muestras y desempate estable.
            domain_scores[label] += 0.01 * float(hits)
        for matched_domain in matched_domains[:2]:
            if matched_domain in domain_scores:
                domain_scores[matched_domain] += 0.001
        candidate_domains = [
            label
            for label, _ in sorted(
                domain_scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        # Deteccion de singleton clusters (outliers operativos).
        cluster_sizes: dict[int, int] = Counter(int(cluster_id) for cluster_id in assignments)
        singleton_clusters = sorted(
            cluster_id for cluster_id, size in cluster_sizes.items() if int(size) == 1
        )

        quality = cls._evaluate_clustering(
            true_labels=sample_labels,
            cluster_ids=assignments,
            beta=f_beta,
        )
        rerank_recommended = (
            1
            if candidate_domains
            and top_confidence >= float(settings.CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE)
            else 0
        )
        trace = {
            "cluster_enabled": "1",
            "cluster_method": method,
            "cluster_k_selected": str(best_run["k"]),
            "cluster_k_min": str(effective_k_min),
            "cluster_k_max": str(effective_k_max),
            "cluster_top_id": str(top_cluster_id),
            "cluster_top_confidence": f"{top_confidence:.4f}",
            "cluster_margin_top2": f"{margin_top2:.4f}",
            "cluster_entropy": f"{entropy:.4f}",
            "cluster_candidate_domains": (
                ",".join(candidate_domains[:6]) if candidate_domains else "none"
            ),
            "cluster_singletons": str(len(singleton_clusters)),
            "cluster_rss": f"{float(best_run['rss']):.4f}",
            "cluster_aic": f"{float(best_run['aic']):.4f}",
            "cluster_purity": f"{quality['purity']:.4f}",
            "cluster_nmi": f"{quality['nmi']:.4f}",
            "cluster_rand_index": f"{quality['rand_index']:.4f}",
            "cluster_f_measure": f"{quality['f_measure']:.4f}",
            "cluster_vocab_size": str(len(idf)),
            "cluster_training_docs": str(n_samples),
            "cluster_rerank_recommended": str(rerank_recommended),
        }
        return {
            "enabled": True,
            "method": method,
            "k_selected": int(best_run["k"]),
            "top_cluster_id": int(top_cluster_id),
            "top_confidence": round(top_confidence, 4),
            "margin_top2": round(margin_top2, 4),
            "entropy": round(entropy, 4),
            "candidate_domains": candidate_domains[:6],
            "singleton_clusters": singleton_clusters,
            "quality": quality,
            "cluster_probabilities": [
                {"cluster_id": int(cluster_id), "probability": round(probability, 4)}
                for cluster_id, probability in ranked_clusters[:6]
            ],
            "trace": trace,
            "memory_facts": [
                f"cluster_top_id:{top_cluster_id}",
                f"cluster_top_confidence:{round(top_confidence, 4)}",
            ],
        }

    @classmethod
    def evaluate_predictions(
        cls,
        *,
        true_labels: list[str],
        cluster_ids: list[int],
        beta: float = 1.0,
    ) -> dict[str, float]:
        """Evalua calidad de clustering plano frente a etiquetas externas."""
        return cls._evaluate_clustering(
            true_labels=[str(item) for item in true_labels],
            cluster_ids=[int(item) for item in cluster_ids],
            beta=float(beta),
        )

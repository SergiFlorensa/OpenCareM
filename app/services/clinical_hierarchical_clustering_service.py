
"""
Clustering jerarquico para priorizacion de dominios clinicos.

Incluye:
- HAC (single/complete/average)
- divisive top-down
- buckshot (muestra HAC + asignacion global)
"""
from __future__ import annotations

import heapq
import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from app.core.config import settings


class ClinicalHierarchicalClusteringService:
    """Servicio de clustering jerarquico para enrutado clinico."""

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)
    _QUERY_SOFTMAX_SCALE = 4.0

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
    def _mean_vector(cls, *, vectors: list[dict[str, float]]) -> dict[str, float]:
        if not vectors:
            return {}
        sums: dict[str, float] = defaultdict(float)
        for vector in vectors:
            for term, value in vector.items():
                sums[term] += float(value)
        averaged = {term: float(value) / float(len(vectors)) for term, value in sums.items()}
        return cls._l2_normalize(averaged)

    @staticmethod
    def _merge_vectors(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
        if not left:
            return dict(right)
        if not right:
            return dict(left)
        merged = dict(left)
        for term, value in right.items():
            merged[term] = float(merged.get(term, 0.0)) + float(value)
        return merged

    @classmethod
    def _pairwise_similarity_matrix(
        cls,
        *,
        vectors: list[dict[str, float]],
    ) -> list[list[float]]:
        n = len(vectors)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        for left in range(n):
            matrix[left][left] = 1.0
            for right in range(left + 1, n):
                sim = cls._dot(vectors[left], vectors[right])
                matrix[left][right] = sim
                matrix[right][left] = sim
        return matrix

    @classmethod
    def _cluster_similarity(
        cls,
        *,
        linkage: str,
        left_members: list[int],
        right_members: list[int],
        pairwise_matrix: list[list[float]],
        left_sum_vector: dict[str, float],
        right_sum_vector: dict[str, float],
    ) -> float:
        if not left_members or not right_members:
            return 0.0
        if linkage == "single":
            best = -1.0
            for left in left_members:
                for right in right_members:
                    best = max(best, float(pairwise_matrix[left][right]))
            return best
        if linkage == "complete":
            best = 1.0
            for left in left_members:
                for right in right_members:
                    best = min(best, float(pairwise_matrix[left][right]))
            return best
        denom = float(len(left_members) * len(right_members))
        if denom <= 0:
            return 0.0
        return cls._safe_div(cls._dot(left_sum_vector, right_sum_vector), denom)

    @classmethod
    def _build_assignments(
        cls,
        *,
        n: int,
        cluster_members: list[list[int]],
    ) -> list[int]:
        assignments = [-1] * n
        for cluster_id, members in enumerate(cluster_members):
            for index in members:
                assignments[int(index)] = int(cluster_id)
        for index, value in enumerate(assignments):
            if value < 0:
                assignments[index] = 0
        return assignments

    @classmethod
    def _run_hac(
        cls,
        *,
        vectors: list[dict[str, float]],
        k: int,
        linkage: str,
    ) -> dict[str, Any]:
        n = len(vectors)
        if n == 0:
            return {
                "cluster_members": [],
                "assignments": [],
                "centroids": [],
                "linkage": linkage,
                "merge_steps": 0,
                "sample_size": 0,
            }

        k = max(1, min(k, n))
        pairwise = cls._pairwise_similarity_matrix(vectors=vectors)
        clusters: dict[int, dict[str, Any]] = {
            index: {
                "members": [index],
                "sum_vector": dict(vectors[index]),
            }
            for index in range(n)
        }
        active_ids: set[int] = set(range(n))
        heap: list[tuple[float, int, int]] = []

        for left in range(n):
            for right in range(left + 1, n):
                sim = cls._cluster_similarity(
                    linkage=linkage,
                    left_members=clusters[left]["members"],
                    right_members=clusters[right]["members"],
                    pairwise_matrix=pairwise,
                    left_sum_vector=clusters[left]["sum_vector"],
                    right_sum_vector=clusters[right]["sum_vector"],
                )
                heapq.heappush(heap, (-float(sim), left, right))

        next_id = n
        merge_steps = 0
        while len(active_ids) > k and heap:
            _, left_id, right_id = heapq.heappop(heap)
            if left_id not in active_ids or right_id not in active_ids:
                continue
            left_cluster = clusters[left_id]
            right_cluster = clusters[right_id]
            merged_members = sorted(left_cluster["members"] + right_cluster["members"])
            merged_sum = cls._merge_vectors(
                left_cluster["sum_vector"],
                right_cluster["sum_vector"],
            )

            active_ids.remove(left_id)
            active_ids.remove(right_id)
            del clusters[left_id]
            del clusters[right_id]

            merged_id = next_id
            next_id += 1
            clusters[merged_id] = {
                "members": merged_members,
                "sum_vector": merged_sum,
            }
            active_ids.add(merged_id)
            merge_steps += 1

            for other_id in list(active_ids):
                if other_id == merged_id:
                    continue
                sim = cls._cluster_similarity(
                    linkage=linkage,
                    left_members=clusters[merged_id]["members"],
                    right_members=clusters[other_id]["members"],
                    pairwise_matrix=pairwise,
                    left_sum_vector=clusters[merged_id]["sum_vector"],
                    right_sum_vector=clusters[other_id]["sum_vector"],
                )
                heapq.heappush(
                    heap,
                    (-float(sim), min(merged_id, other_id), max(merged_id, other_id)),
                )

        final_ids = sorted(active_ids, key=lambda cid: min(clusters[cid]["members"]))
        cluster_members = [list(clusters[cid]["members"]) for cid in final_ids]
        assignments = cls._build_assignments(n=n, cluster_members=cluster_members)
        centroids = [
            cls._mean_vector(vectors=[vectors[index] for index in members])
            for members in cluster_members
        ]
        return {
            "cluster_members": cluster_members,
            "assignments": assignments,
            "centroids": centroids,
            "linkage": linkage,
            "merge_steps": merge_steps,
            "sample_size": n,
            "strategy": f"hac_{linkage}",
        }

    @classmethod
    def _bisect_cluster(
        cls,
        *,
        vectors: list[dict[str, float]],
        members: list[int],
        pairwise_matrix: list[list[float]],
        iterations: int = 4,
    ) -> tuple[list[int], list[int]]:
        if len(members) <= 1:
            return list(members), []
        seed_a = int(members[0])
        seed_b = int(max(members[1:], key=lambda idx: pairwise_matrix[seed_a][idx]))
        centroid_a = dict(vectors[seed_a])
        centroid_b = dict(vectors[seed_b])

        left_members: list[int] = []
        right_members: list[int] = []
        for _ in range(max(1, iterations)):
            left_members = []
            right_members = []
            for index in members:
                sim_left = cls._dot(vectors[index], centroid_a)
                sim_right = cls._dot(vectors[index], centroid_b)
                if sim_left >= sim_right:
                    left_members.append(index)
                else:
                    right_members.append(index)

            if not left_members or not right_members:
                half = max(1, len(members) // 2)
                left_members = sorted(members[:half])
                right_members = sorted(members[half:])
                if not right_members:
                    right_members = [left_members.pop()]
                break

            centroid_a = cls._mean_vector(vectors=[vectors[idx] for idx in left_members])
            centroid_b = cls._mean_vector(vectors=[vectors[idx] for idx in right_members])
        return sorted(left_members), sorted(right_members)

    @classmethod
    def _run_divisive(
        cls,
        *,
        vectors: list[dict[str, float]],
        k: int,
    ) -> dict[str, Any]:
        n = len(vectors)
        if n == 0:
            return {
                "cluster_members": [],
                "assignments": [],
                "centroids": [],
                "linkage": "average",
                "merge_steps": 0,
                "sample_size": 0,
                "strategy": "divisive",
            }
        k = max(1, min(k, n))
        pairwise = cls._pairwise_similarity_matrix(vectors=vectors)
        cluster_members: list[list[int]] = [list(range(n))]
        split_steps = 0

        while len(cluster_members) < k:
            candidate_index = -1
            candidate_score = -1.0
            for index, members in enumerate(cluster_members):
                if len(members) <= 1:
                    continue
                sims = [
                    pairwise[members[left]][members[right]]
                    for left in range(len(members))
                    for right in range(left + 1, len(members))
                ]
                avg_similarity = (
                    sum(float(item) for item in sims) / float(len(sims)) if sims else 1.0
                )
                spread = 1.0 - avg_similarity
                if spread > candidate_score:
                    candidate_score = spread
                    candidate_index = index
            if candidate_index < 0:
                break

            members = cluster_members.pop(candidate_index)
            left_members, right_members = cls._bisect_cluster(
                vectors=vectors,
                members=members,
                pairwise_matrix=pairwise,
            )
            if not left_members or not right_members:
                cluster_members.append(members)
                break
            cluster_members.append(left_members)
            cluster_members.append(right_members)
            split_steps += 1

        cluster_members = sorted(cluster_members, key=lambda members: min(members))
        assignments = cls._build_assignments(n=n, cluster_members=cluster_members)
        centroids = [
            cls._mean_vector(vectors=[vectors[index] for index in members])
            for members in cluster_members
        ]
        return {
            "cluster_members": cluster_members,
            "assignments": assignments,
            "centroids": centroids,
            "linkage": "average",
            "merge_steps": split_steps,
            "sample_size": n,
            "strategy": "divisive",
        }

    @classmethod
    def _run_buckshot(
        cls,
        *,
        vectors: list[dict[str, float]],
        k: int,
        linkage: str = "average",
        sample_scale: float = 1.0,
    ) -> dict[str, Any]:
        n = len(vectors)
        if n == 0:
            return {
                "cluster_members": [],
                "assignments": [],
                "centroids": [],
                "linkage": linkage,
                "merge_steps": 0,
                "sample_size": 0,
                "strategy": "buckshot",
            }
        k = max(1, min(k, n))
        sample_target = int(round(math.sqrt(float(n)) * max(0.5, float(sample_scale))))
        sample_size = max(k, min(n, sample_target))
        if sample_size >= n:
            sample_indices = list(range(n))
        else:
            sample_indices = []
            used: set[int] = set()
            for slot in range(sample_size):
                index = int((slot * n) / sample_size)
                while index in used and index + 1 < n:
                    index += 1
                if index in used:
                    index = slot % n
                sample_indices.append(index)
                used.add(index)

        sample_vectors = [vectors[index] for index in sample_indices]
        sample_hac = cls._run_hac(vectors=sample_vectors, k=k, linkage=linkage)
        sample_clusters = list(sample_hac["cluster_members"])
        centroids: list[dict[str, float]] = []
        for members in sample_clusters:
            global_members = [sample_indices[index] for index in members]
            centroid = cls._mean_vector(vectors=[vectors[index] for index in global_members])
            centroids.append(centroid)

        if not centroids:
            centroids = [dict(vectors[0])]

        assignments = [0] * n
        for row_id, vector in enumerate(vectors):
            best_cluster = 0
            best_similarity = -1.0
            for cluster_id, centroid in enumerate(centroids):
                similarity = cls._dot(vector, centroid)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_cluster = cluster_id
            assignments[row_id] = int(best_cluster)

        cluster_members: list[list[int]] = [[] for _ in range(len(centroids))]
        for row_id, cluster_id in enumerate(assignments):
            cluster_members[int(cluster_id)].append(row_id)

        centroids = [
            cls._mean_vector(vectors=[vectors[index] for index in members]) if members else {}
            for members in cluster_members
        ]
        cluster_members = [members for members in cluster_members if members]
        centroids = [centroids[idx] for idx, members in enumerate(cluster_members) if members]
        assignments = cls._build_assignments(n=n, cluster_members=cluster_members)
        return {
            "cluster_members": cluster_members,
            "assignments": assignments,
            "centroids": centroids,
            "linkage": linkage,
            "merge_steps": int(sample_hac.get("merge_steps") or 0),
            "sample_size": sample_size,
            "strategy": "buckshot",
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

        contingency = [[0 for _ in class_labels] for _ in clusters]
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
        for col_id in range(len(class_labels)):
            class_size = class_totals[col_id]
            if class_size <= 0:
                continue
            best_f = 0.0
            for row_id in range(len(clusters)):
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
    def _build_cluster_labels(
        cls,
        *,
        cluster_members: list[list[int]],
        sample_labels: list[str],
        sample_tokens: list[list[str]],
    ) -> list[dict[str, Any]]:
        all_indices = list(range(len(sample_labels)))
        labels: list[dict[str, Any]] = []
        for cluster_id, members in enumerate(cluster_members):
            member_set = set(int(index) for index in members)
            other_indices = [index for index in all_indices if index not in member_set]
            dominant_domain = ""
            if members:
                dominant_domain = (
                    Counter(sample_labels[index] for index in members).most_common(1)[0][0]
                )
            in_counter: Counter[str] = Counter()
            out_counter: Counter[str] = Counter()
            in_total = 0
            out_total = 0
            for index in members:
                tokens = sample_tokens[index]
                in_total += len(tokens)
                in_counter.update(tokens)
            for index in other_indices:
                tokens = sample_tokens[index]
                out_total += len(tokens)
                out_counter.update(tokens)

            scored_terms: list[tuple[str, float]] = []
            for term, in_count in in_counter.items():
                in_rate = cls._safe_div(in_count, max(1, in_total))
                out_rate = cls._safe_div(out_counter.get(term, 0), max(1, out_total))
                score = in_rate - out_rate
                if score > 0:
                    scored_terms.append((term, float(score)))
            scored_terms.sort(key=lambda item: (item[1], item[0]), reverse=True)
            labels.append(
                {
                    "cluster_id": int(cluster_id),
                    "size": len(members),
                    "dominant_domain": dominant_domain,
                    "top_terms": [term for term, _ in scored_terms[:3]],
                }
            )
        return labels

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        domain_catalog: list[dict[str, object]],
        matched_domains: list[str],
        effective_specialty: str,  # noqa: ARG003 - reservado para calibraciones futuras
    ) -> dict[str, Any]:
        method = str(settings.CLINICAL_CHAT_HCLUSTER_METHOD).strip().lower()
        k_min = int(settings.CLINICAL_CHAT_HCLUSTER_K_MIN)
        k_max = int(settings.CLINICAL_CHAT_HCLUSTER_K_MAX)
        min_confidence = float(settings.CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE)
        f_beta = float(settings.CLINICAL_CHAT_HCLUSTER_F_BETA)
        buckshot_scale = float(settings.CLINICAL_CHAT_HCLUSTER_BUCKSHOT_SAMPLE_SCALE)
        max_candidates = int(settings.CLINICAL_CHAT_HCLUSTER_MAX_CANDIDATE_DOMAINS)

        disabled_payload = {
            "enabled": False,
            "method": method,
            "strategy": method,
            "linkage": "average",
            "k_selected": 0,
            "top_cluster_id": -1,
            "top_confidence": 0.0,
            "margin_top2": 0.0,
            "entropy": 0.0,
            "candidate_domains": [],
            "singleton_clusters": [],
            "cluster_labels": [],
            "quality": {
                "purity": 0.0,
                "nmi": 0.0,
                "rand_index": 0.0,
                "f_measure": 0.0,
            },
            "trace": {
                "hcluster_enabled": "0",
                "hcluster_method": method,
                "hcluster_strategy": method,
                "hcluster_linkage": "average",
                "hcluster_k_selected": "0",
                "hcluster_k_min": str(k_min),
                "hcluster_k_max": str(k_max),
                "hcluster_top_id": "-1",
                "hcluster_top_confidence": "0.0",
                "hcluster_margin_top2": "0.0",
                "hcluster_entropy": "0.0",
                "hcluster_candidate_domains": "none",
                "hcluster_singletons": "0",
                "hcluster_merge_steps": "0",
                "hcluster_sample_size": "0",
                "hcluster_purity": "0.0",
                "hcluster_nmi": "0.0",
                "hcluster_rand_index": "0.0",
                "hcluster_f_measure": "0.0",
                "hcluster_vocab_size": "0",
                "hcluster_training_docs": "0",
                "hcluster_rerank_recommended": "0",
            },
            "memory_facts": [],
        }
        if not settings.CLINICAL_CHAT_HCLUSTER_ENABLED:
            return disabled_payload

        samples = cls._build_training_samples(domain_catalog=domain_catalog)
        if not samples:
            return disabled_payload

        sample_labels = [label for label, _ in samples]
        sample_tokens = [tokens for _, tokens in samples]
        idf = cls._compute_idf(samples=samples)
        sample_vectors = [cls._vectorize_tokens(tokens=tokens, idf=idf) for tokens in sample_tokens]
        n_samples = len(sample_vectors)
        if n_samples == 0:
            return disabled_payload

        effective_k_min = max(1, min(k_min, n_samples))
        effective_k_max = max(effective_k_min, min(k_max, n_samples))
        candidate_ks = list(range(effective_k_min, effective_k_max + 1))

        best_run: dict[str, Any] | None = None
        best_objective = float("-inf")
        linkage = "average"
        strategy = method
        for k in candidate_ks:
            if method in {"hac_single", "hac_complete", "hac_average"}:
                linkage = method.split("_", maxsplit=1)[1]
                run = cls._run_hac(vectors=sample_vectors, k=k, linkage=linkage)
                strategy = f"hac_{linkage}"
            elif method == "divisive":
                run = cls._run_divisive(vectors=sample_vectors, k=k)
                linkage = "average"
                strategy = "divisive"
            else:
                run = cls._run_buckshot(
                    vectors=sample_vectors,
                    k=k,
                    linkage="average",
                    sample_scale=buckshot_scale,
                )
                linkage = "average"
                strategy = "buckshot"

            quality = cls._evaluate_clustering(
                true_labels=sample_labels,
                cluster_ids=run["assignments"],
                beta=f_beta,
            )
            objective = (
                (0.50 * float(quality["f_measure"]))
                + (0.30 * float(quality["nmi"]))
                + (0.20 * float(quality["purity"]))
            )
            objective -= 0.005 * float(max(0, k - effective_k_min))
            if objective > best_objective:
                best_objective = objective
                best_run = {
                    **run,
                    "k": k,
                    "quality": quality,
                    "objective": objective,
                    "linkage": linkage,
                    "strategy": strategy,
                }

        if best_run is None:
            return disabled_payload

        assignments = list(best_run["assignments"])
        centroids = list(best_run["centroids"])
        cluster_members = list(best_run["cluster_members"])
        quality = dict(best_run["quality"])

        query_tokens = cls._tokenize(query)
        query_vector = cls._vectorize_tokens(tokens=query_tokens, idf=idf)
        centroid_scores = {
            str(cluster_id): cls._dot(query_vector, centroid) * cls._QUERY_SOFTMAX_SCALE
            for cluster_id, centroid in enumerate(centroids)
        }
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

        domain_scores: dict[str, float] = defaultdict(float)
        domain_hits: dict[str, int] = defaultdict(int)
        if top_cluster_id >= 0:
            top_members = (
                cluster_members[top_cluster_id]
                if top_cluster_id < len(cluster_members)
                else []
            )
            for row_id in top_members:
                label = sample_labels[row_id]
                similarity = cls._dot(query_vector, sample_vectors[row_id])
                domain_scores[label] += max(0.0, float(similarity))
                domain_hits[label] += 1
        for label, hits in domain_hits.items():
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

        cluster_sizes: dict[int, int] = Counter(int(cluster_id) for cluster_id in assignments)
        singleton_clusters = sorted(
            cluster_id for cluster_id, size in cluster_sizes.items() if int(size) == 1
        )
        cluster_labels = cls._build_cluster_labels(
            cluster_members=cluster_members,
            sample_labels=sample_labels,
            sample_tokens=sample_tokens,
        )
        rerank_recommended = (
            1
            if candidate_domains and top_confidence >= float(min_confidence)
            else 0
        )

        trace = {
            "hcluster_enabled": "1",
            "hcluster_method": method,
            "hcluster_strategy": str(best_run.get("strategy") or strategy),
            "hcluster_linkage": str(best_run.get("linkage") or linkage),
            "hcluster_k_selected": str(best_run["k"]),
            "hcluster_k_min": str(effective_k_min),
            "hcluster_k_max": str(effective_k_max),
            "hcluster_top_id": str(top_cluster_id),
            "hcluster_top_confidence": f"{top_confidence:.4f}",
            "hcluster_margin_top2": f"{margin_top2:.4f}",
            "hcluster_entropy": f"{entropy:.4f}",
            "hcluster_candidate_domains": (
                ",".join(candidate_domains[:max_candidates]) if candidate_domains else "none"
            ),
            "hcluster_singletons": str(len(singleton_clusters)),
            "hcluster_merge_steps": str(int(best_run.get("merge_steps") or 0)),
            "hcluster_sample_size": str(int(best_run.get("sample_size") or 0)),
            "hcluster_purity": f"{quality['purity']:.4f}",
            "hcluster_nmi": f"{quality['nmi']:.4f}",
            "hcluster_rand_index": f"{quality['rand_index']:.4f}",
            "hcluster_f_measure": f"{quality['f_measure']:.4f}",
            "hcluster_vocab_size": str(len(idf)),
            "hcluster_training_docs": str(n_samples),
            "hcluster_rerank_recommended": str(rerank_recommended),
        }
        return {
            "enabled": True,
            "method": method,
            "strategy": str(best_run.get("strategy") or strategy),
            "linkage": str(best_run.get("linkage") or linkage),
            "k_selected": int(best_run["k"]),
            "top_cluster_id": int(top_cluster_id),
            "top_confidence": round(top_confidence, 4),
            "margin_top2": round(margin_top2, 4),
            "entropy": round(entropy, 4),
            "candidate_domains": candidate_domains[:max_candidates],
            "singleton_clusters": singleton_clusters,
            "cluster_labels": cluster_labels,
            "quality": quality,
            "cluster_probabilities": [
                {"cluster_id": int(cluster_id), "probability": round(probability, 4)}
                for cluster_id, probability in ranked_clusters[:6]
            ],
            "trace": trace,
            "memory_facts": [
                f"hcluster_top_id:{top_cluster_id}",
                f"hcluster_top_confidence:{round(top_confidence, 4)}",
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
        """Evalua calidad de clustering jerarquico frente a etiquetas externas."""
        return cls._evaluate_clustering(
            true_labels=[str(item) for item in true_labels],
            cluster_ids=[int(item) for item in cluster_ids],
            beta=float(beta),
        )

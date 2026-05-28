package cn.techkg.common.controller;

import io.milvus.client.MilvusServiceClient;
import io.milvus.grpc.CheckHealthResponse;
import org.apache.kafka.clients.admin.AdminClient;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.*;

@RestController
@RequestMapping("/health")
public class HealthController {

    private static final long CHECK_TIMEOUT_SECONDS = 5;

    private final JdbcTemplate jdbcTemplate;
    private final RedisTemplate<String, Object> redisTemplate;
    private final ObjectProvider<MilvusServiceClient> milvusClientProvider;
    private final ObjectProvider<AdminClient> kafkaAdminClientProvider;
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

    public HealthController(JdbcTemplate jdbcTemplate,
                            RedisTemplate<String, Object> redisTemplate,
                            ObjectProvider<MilvusServiceClient> milvusClientProvider,
                            ObjectProvider<AdminClient> kafkaAdminClientProvider) {
        this.jdbcTemplate = jdbcTemplate;
        this.redisTemplate = redisTemplate;
        this.milvusClientProvider = milvusClientProvider;
        this.kafkaAdminClientProvider = kafkaAdminClientProvider;
    }

    @GetMapping
    public Map<String, Object> health() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("mysql", checkMySQL());
        result.put("redis", checkRedis());
        result.put("milvus", checkMilvus());
        result.put("kafka", checkKafka());
        return result;
    }

    private Map<String, Object> checkMySQL() {
        try {
            return executor.submit(() -> {
                String version = jdbcTemplate.queryForObject("SELECT VERSION()", String.class);
                return Map.of("status", "UP", "version", (Object) version);
            }).get(CHECK_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            return Map.of("status", "DOWN", "error", "timeout");
        } catch (Exception e) {
            return Map.of("status", "DOWN", "error", unwrapMessage(e));
        }
    }

    private Map<String, Object> checkRedis() {
        try {
            return executor.submit(() -> {
                String pong = redisTemplate.getConnectionFactory().getConnection().ping();
                return Map.of("status", "UP", "response", (Object) pong);
            }).get(CHECK_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            return Map.of("status", "DOWN", "error", "timeout");
        } catch (Exception e) {
            return Map.of("status", "DOWN", "error", unwrapMessage(e));
        }
    }

    private Map<String, Object> checkMilvus() {
        try {
            return executor.submit(() -> {
                MilvusServiceClient client = milvusClientProvider.getObject();
                CheckHealthResponse resp = client.checkHealth().getData();
                return Map.of("status", resp.getIsHealthy() ? "UP" : "DOWN", "reason", (Object) resp.getReasonsList());
            }).get(CHECK_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            return Map.of("status", "DOWN", "error", "timeout");
        } catch (Exception e) {
            return Map.of("status", "DOWN", "error", unwrapMessage(e));
        }
    }

    private Map<String, Object> checkKafka() {
        try {
            return executor.submit(() -> {
                AdminClient adminClient = kafkaAdminClientProvider.getObject();
                String clusterId = adminClient.describeCluster().clusterId().get(CHECK_TIMEOUT_SECONDS, TimeUnit.SECONDS);
                return Map.of("status", "UP", "clusterId", (Object) clusterId);
            }).get(CHECK_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        } catch (TimeoutException e) {
            return Map.of("status", "DOWN", "error", "timeout");
        } catch (Exception e) {
            return Map.of("status", "DOWN", "error", unwrapMessage(e));
        }
    }

    private String unwrapMessage(Exception e) {
        Throwable cause = e.getCause();
        return cause != null ? cause.getMessage() : e.getMessage();
    }
}

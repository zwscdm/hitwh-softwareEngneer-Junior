package edu.hitwh.repository;

import java.util.List;

/**
 * 订单存储接口，订单与数据存储相关的内容
 */
public interface OrderRepo {
    List<String> findAll();
}

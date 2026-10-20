package edu.hitwh.test;

import edu.hitwh.context.AnnotationConfigApplicationContext;
import edu.hitwh.context.BeanDefination;

import java.util.Set;

public class Main {
    public static void main(String[] args) {
        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext("edu.hitwh");
        Set<BeanDefination> beanDefinations = context.getBeanDefinations();
        for (BeanDefination beanDefination : beanDefinations) {
            System.out.println(beanDefination);
        }
    }
}

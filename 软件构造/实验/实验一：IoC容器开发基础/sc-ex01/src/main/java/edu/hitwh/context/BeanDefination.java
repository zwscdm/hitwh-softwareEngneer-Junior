package edu.hitwh.context;

/**
 * 需要被IoC容器管理的bean的基本信息
 */
public class BeanDefination {
    private String beanName; // Bean的名字
    private Class beanClass; // Bean的Class对象

    public BeanDefination(String beanName, Class beanClass) {
        this.beanName = beanName;
        this.beanClass = beanClass;
    }

    public String getBeanName() {
        return beanName;
    }

    public void setBeanName(String beanName) {
        this.beanName = beanName;
    }

    public Class getBeanClass() {
        return beanClass;
    }

    public void setBeanClass(Class beanClass) {
        this.beanClass = beanClass;
    }

    @Override
    public String toString() {
        return "BeanDefination{" +
                "beanName='" + beanName + '\'' +
                ", beanClass=" + beanClass +
                '}';
    }
}
